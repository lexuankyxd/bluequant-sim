import sys
import os
import importlib.util
import xml.etree.ElementTree as ET
import BUtils
import numpy as np
from threading import Thread, Semaphore, Lock
import json
from BDataUtils import patch_data
from timeit import default_timer
NAN = float('nan')

showInput = sys.argv[2]


def get_module_method(filename, method_name):
    spec = importlib.util.spec_from_file_location("module", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    method = getattr(module, method_name)
    return method


def get_module_method(filename, method_name):
    spec = importlib.util.spec_from_file_location("module", filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    method = getattr(module, method_name)
    return method


def init_global_variables(global_data):
    global_data["id_set"] = set()


def load_params(global_data, node):
    if (node is None):
        raise Exception("No PARAMS tag in XML doc!")
    global_data["data_dir"] = BUtils.format_path(
        BUtils.get_compulsory_attr(node, "data_dir", "Params"))
    global_data["start_date"] = int(
        BUtils.get_compulsory_attr(node, "start_date", "Params"))
    global_data["end_date"] = int(
        BUtils.get_compulsory_attr(node, "end_date", "Params"))
    global_data["back_days"] = int(
        BUtils.get_compulsory_attr(node, "back_days", "Params"))

    global_data["interval"] = node.get("interval", "daily")
    global_data["daily_start_time"] = int(
        node.get("daily_start_time", "000000"))

    global_data["delay"] = int(node.get("delay", "1"))


def load_data_module(global_data, node):
    print("Loaded data", node.get("id"))
    processor_path = BUtils.get_compulsory_attr(node, "processor", node.tag)
    build_method = get_module_method(processor_path, "build_data")
    build_method(node, global_data)


def load_data_pool(global_data, node):
    if (node is None):
        raise Exception("DataPool tag not found in XML file!")
    cc = 0
    print("Loading data pool")
    for child in node.findall("Data"):
        load_data_module(global_data, child)
        cc += 1
    if (cc == 0):
        raise Exception("Empty data pool!")


def load_transformer(global_data, node, run_class):
    processor_path = BUtils.get_compulsory_attr(node, "processor", run_class)
    Class = get_module_method(processor_path, run_class)
    t = Class()
    t.create(global_data, node)
    return t


def load_transformers(global_data, node, run_class):
    transformers = []
    if (node is None):
        return transformers
    for child in node.findall(run_class):
        transformers.append(load_transformer(global_data, child, run_class))
    return transformers


def load_alpha_module(global_data, node, run_class):
    id = BUtils.get_compulsory_attr(node, "id", run_class)
    processor_path = BUtils.get_compulsory_attr(node, "processor", id)
    AlphaClass = get_module_method(processor_path, run_class)
    alp = AlphaClass()
    alp.id = id
    alp.booksize = float(node.get("booksize", "1e+6"))
    alp.create(global_data, node)
    alp.transformers = load_transformers(
        global_data, node.find("Transforms"), "Transform")
    return alp


def load_alpha_modules(global_data, node, run_class):
    modules = []
    global_data["u_close"] = patch_data(global_data["close"].T)
    global_data["u_open"] = patch_data(global_data["open"].T)
    global_data["u_high"] = patch_data(global_data["high"].T)
    global_data["u_low"] = patch_data(global_data["low"].T)
    global_data["u_volume"] = patch_data(global_data["volume"].T)

    for child in node.findall(run_class):
        days = [int(i) for i in child.attrib['days'].split(" ")]
        modes = [int(i) for i in child.attrib['mode'].split(" ")]
        id = child.attrib["id"]
        for i in range(len(days)):
            for j in range(len(modes)):
                child.attrib['id'] = id + "_d" + \
                    str(days[i]) + "_m" + str(modes[j])
                child.attrib["days"] = days[i]
                child.attrib["mode"] = modes[j]
                modules.append(load_alpha_module(
                    global_data, child, run_class))

    print("No of", run_class, len(modules))
    return modules


def check_duplicate_alpha_id(alphas):
    id_set = set()
    for alpha in alphas:
        if (alpha.id in id_set):
            raise Exception("Error: Duplicate alpha id " + alpha.id)
        id_set.add(alpha.id)


def load_trade_module(global_data, node, run_class, alphas):
    id = BUtils.get_compulsory_attr(node, "id", run_class)
    processor_path = BUtils.get_compulsory_attr(node, "processor", id)
    Class = get_module_method(processor_path, run_class)
    for alpha in alphas:
        obj = Class()
        obj.alpha_id = alpha.id
        obj.create(global_data, node)
        alpha.trade_modules.append(obj)


def load_trade_modules(global_data, node, run_class, alphas):
    cc = 0
    for child in node.findall(run_class):
        load_trade_module(global_data, child, run_class, alphas)
        cc += 1
    print("No of", run_class, cc)


def run_alpha(a, di):
    for ii in range(len(a.alpha)):
        a.alpha[ii] = NAN
    a.generate(di)
    # print(a.alpha)
    for t in a.transformers:
        t.transform(a.alpha)
    BUtils.scale_to_booksize(a.alpha, a.booksize)
    # print(a.alpha)


def run_single_thread(global_data, alphas):
    start_di = global_data["start_sim_di"]
    end_di = global_data["end_sim_di"]
    for di in range(start_di, end_di+1):
        for a in alphas:
            run_alpha(a, di)
            for trade in a.trade_modules:

                temp = trade.calculate(di, a)
                if showInput == '1':
                    print(temp)
            for ii in range(len(a.alpha)):
                a.prev_alpha[ii] = a.alpha[ii]

    for a in alphas:
        for trade in a.trade_modules:
            trade.finish()


def sim_thread_run(alphas, start_di, end_di, status_di, run_lock, print_lock):
    num_alphas = len(alphas)
    min_ai = -1
    while True:
        run_lock.acquire()
        if (min_ai >= 0):
            status_di[min_ai] = (-status_di[min_ai]) + 1
        min_di = end_di + 1
        for i in range(num_alphas):
            if (status_di[i] >= 0) and (min_di > status_di[i]):
                min_ai = i
                min_di = status_di[i]
        if (min_di > end_di):
            run_lock.release()
            break
        di = status_di[min_ai]
        status_di[min_ai] = -di
        run_lock.release()

        a = alphas[min_ai]
        run_alpha(a, di)
        output = ""
        for trade in a.trade_modules:
            if (len(output) > 0):
                output += "\n"
            output += trade.calculate(di, a)
        print_lock.acquire()
        if showInput == '1':
            print(output)
        print_lock.release()
        for ii in range(len(a.alpha)):
            a.prev_alpha[ii] = a.alpha[ii]


def run_multi_thread(global_data, alphas, num_threads):
    start_di = global_data["start_sim_di"]
    end_di = global_data["end_sim_di"]
    run_lock = Lock()
    print_lock = Lock()
    status_di = [start_di] * len(alphas)

    threads = []
    for i in range(num_threads):
        t = Thread(target=sim_thread_run, args=(
            alphas, start_di, end_di, status_di, run_lock, print_lock))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    for a in alphas:
        for trade in a.trade_modules:
            trade.finish()


def sim_thread_run2(a, semaphore, start_di, end_di, print_lock):
    for di in range(start_di, end_di+1):
        semaphore.acquire()
        run_alpha(a, di)
        output = ""
        for trade in a.trade_modules:
            if (len(output) > 0):
                output += "\n"
            output += trade.calculate(di, a)
        print_lock.acquire()
        if showInput == '1':
            print(output)
        print_lock.release()
        for ii in range(len(a.alpha)):
            a.prev_alpha[ii] = a.alpha[ii]
        semaphore.release()


def run_multi_thread2(global_data, alphas, num_threads):
    start_di = global_data["start_sim_di"]
    end_di = global_data["end_sim_di"]
    run_semaphore = Semaphore(num_threads)
    print_lock = Lock()

    threads = []
    for a in alphas:
        t = Thread(target=sim_thread_run2, args=(
            a, run_semaphore, start_di, end_di, print_lock))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    for a in alphas:
        for trade in a.trade_modules:
            trade.finish()


def run_simulation(global_data, node):
    if (node is None):
        raise Exception("Simulation tag not found in XML file!")
    processor_path = node.get("processor")
    if (processor_path is not None):  # custom simulation
        sim_run = get_module_method(processor_path, "sim_run")
        sim_run(global_data, node)
        return

    alphas = load_alpha_modules(
        global_data, node.find("AlphaModules"), "Alpha")
    check_duplicate_alpha_id(alphas)

    alpha_size = len(global_data["tickers"])
    for a in alphas:
        a.trade_modules = []
        a.alpha = np.zeros((alpha_size), dtype=np.float32)
        a.prev_alpha = np.zeros((alpha_size), dtype=np.float32)
    load_trade_modules(global_data, node.find("TradeModules"), "Trade", alphas)
    num_threads = int(node.get("num_threads", 1))
    if (num_threads == 1):
        run_single_thread(global_data, alphas)
    else:
        run_multi_thread(global_data, alphas, num_threads)


def BSim_Main(config_filename):
    os.system("rm pnl/*")
    global_data = BUtils.BDict()  # all global data, variable, constants, ...
    xml_doc = ET.parse(config_filename)
    xml_root_node = xml_doc.getroot()
    init_global_variables(global_data)
    load_params(global_data, xml_root_node.find("Params"))
    print("Loading constants DONE")

    load_data_pool(global_data, xml_root_node.find("DataPool"))
    print("Loading data pool DONE")
    start = default_timer()
    run_simulation(global_data, xml_root_node.find("Simulation"))
    print("Time ran: ", default_timer() - start)


BSim_Main(sys.argv[1])

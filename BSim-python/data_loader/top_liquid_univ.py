import math
import BUtils
import BDataUtils
import numpy as np


def build_data(xml_node, global_data):
    id, data_dir = BUtils.get_basic_attrs(xml_node, global_data)
    days = int(xml_node.get("days", 20))
    min_adv = float((xml_node.get("min_adv", 1e+6)))

    meta_info = str([global_data["data_version"], days, min_adv])
    old_shape = BDataUtils.get_reusable_data_shape(data_dir, meta_info)

    dates = global_data["dates"]
    tickers = global_data["tickers"]
    num_days = len(dates)
    num_tickers = len(tickers)
    data_infos = []
    valid = BDataUtils.register_data(
        global_data, data_infos, data_dir, id, bool, old_shape, (num_days, num_tickers), False)

    di_start = old_shape[0]
    if (di_start == num_days):
        return

    close = global_data["close"]
    volume = global_data["volume"]
    target_vol = min_adv * days
    for di in range(di_start, num_days):
        if (di <= days):
            for ii in range(num_tickers):
                valid[di][ii] = False
            continue
        cc = 0
        for ii in range(num_tickers):
            sum = 0
            for d in range(di-days, di-1):
                sum += close[d][ii] * volume[d][ii]
            valid[di][ii] = (sum > target_vol)
            if (valid[di][ii]):
                cc += 1
        print("[" + id + "]:", dates[di], "No of valids", cc)

    BUtils.create_dir(data_dir)
    meta_lines = [meta_info, num_days, num_tickers]
    BDataUtils.save_meta_file(data_dir, meta_lines)
    BDataUtils.save_all_register_data(data_dir, data_infos)


def test_data(global_data, id):
    valid = global_data[id]
    dates = global_data["dates"]
    tickers = global_data["tickers"]
    num_days = len(dates)
    num_tickers = len(tickers)
    for di in range(num_days):
        print(dates[di], valid[di][:])

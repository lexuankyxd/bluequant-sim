import numpy as np
import BUtils
import BDataUtils
import os
import bisect
import math
import random

NAN = float('nan')


def check_meta_valid(meta_info, data_start_date, meta_lines):
    try:
        if (len(meta_lines) < 3):
            return False
        if (meta_info != meta_lines[0]):
            return False
        current_data_start = int(meta_lines[1])
        if (current_data_start > data_start_date):
            return False
    except:
        return False
    return True


def get_daily_data_dates_sorted(daily_data_path):
    data_dates = []
    for filename in os.listdir(path=daily_data_path):
        if filename.endswith(".csv"):
            d = int(filename[0:-4])
            data_dates.append(d)
    return sorted(data_dates)


def load_daily_data(data_path, date, output):
    lines = BUtils.load_text_file(data_path + "/" + str(date) + ".csv")
    for line in lines[1:]:
        read = line.split(",")
        if "-" in read[1]:
            temp = read[1].split("-")
            read[1] = ""
            for i in temp:
                read[1] += i
        read[1] = int(read[1])
        # read[7] = int(read[7])
        output.append(read)


def aggregate_open(a, b):
    return a


def aggregate_close(a, b):
    return b


def aggregate_low(a, b):
    if (a < b):
        return a
    return b


def aggregate_high(a, b):
    if (a < b):
        return b
    return a


def aggregate_sum(a, b):
    return a+b


def get_aggregate_method(name):
    if (name == "open"):
        return aggregate_open
    if (name == "close"):
        return aggregate_close
    if (name == "high"):
        return aggregate_high
    if (name == "low"):
        return aggregate_low
    return aggregate_sum


def parse_field_map(text):
    output = []
    for s in text.split(" "):
        pair = s.split("=")
        output.append([pair[0], int(pair[1]), get_aggregate_method(pair[0])])
    return output


def update_instruments(instruments, instrument_map, reads):
    n = len(instruments)
    old_n = n
    new_inst = False
    for read in reads:
        ticker = read[0]
        if not (ticker in instrument_map):
            instruments.append(ticker)
            instrument_map[ticker] = n
            n += 1
            new_inst = True
    return new_inst


def resize_data_fields(data_fields, num_days, end_data_di, old_size, new_size):
    for f in data_fields:
        old = f[3]
        data = np.zeros((num_days, new_size), dtype=np.float32)
        f[3] = data
        for d in range(end_data_di):
            for ii in range(old_size):
                data[d][ii] = old[d][ii]
            for ii in range(old_size, new_size):
                data[d][ii] = NAN


def polling_instrument_set(data_path, dates, instruments, instrument_map):
    n = len(dates)
    di = 0
    while (di < n):
        lines = BUtils.load_text_file(
            data_path + "/" + str(dates[di]) + ".csv")
        reads = []
        for s in lines:
            p = s.find(",")
            if (p >= 0):
                s = s[0:p]
            reads.append([s])

        update_instruments(instruments, instrument_map, reads)
        di += 30
    return


def add_data_value(ci, method, data, di, ii, read):
    value = float(read[ci])
    if (math.isnan(value)):
        return
    if (math.isnan(data[di][ii])):
        data[di][ii] = value
    data[di][ii] = method(data[di][ii], value)


def load_and_process_daily_data(data_fields, data_path, instruments, instrument_map, dates, start_time_secs, di_start, extra_date):
    num_days = len(dates)
    num_insts = len(instruments)
    reads = []
    for di in range(di_start, num_days):
        start_time = BUtils.get_date_timestamp(dates[di]) + start_time_secs
        end_time = start_time + 86400

        start_time *= 1000
        end_time *= 1000

        print(start_time_secs, di, di_start)
        if (start_time_secs == 0) or (di == di_start):
            load_daily_data(data_path, dates[di], reads)
        if (start_time_secs > 0):
            if (di+1 < len(dates)):
                load_daily_data(data_path, dates[di+1], reads)
            else:
                load_daily_data(data_path, extra_date, reads)

        if update_instruments(instruments, instrument_map, reads):
            old_size = num_insts
            num_insts = len(instruments)
            resize_data_fields(data_fields, num_days, di, old_size, num_insts)
            print("Update instruments", num_insts)

        for f in data_fields:
            data = f[3]
            for ii in range(num_insts):
                data[di][ii] = NAN

        ri = 0
        while (ri < len(reads)) and (reads[ri][1] < start_time):
            ri += 1

        while (ri < len(reads)) and (reads[ri][1] < end_time):
            read = reads[ri]
            ii = instrument_map[read[0]]
            # if (read[0] == "BTCUSDT") and (dates[di] == 20230121): print(read)
            for f in data_fields:
                add_data_value(f[1], f[2], f[3], di, ii, read)
            ri += 1
        # if (di >= d2):
        #     ii = instrument_map["BTCUSDT"]
        #     for f in data_fields: print(f[0], f[3][d2][ii])
        print("Loaded data on", dates[di], "no of records =", ri)
        reads = reads[ri:]

    return


def build_from_scratch(data_fields, data_path, data_dates, start_date_index, end_date_index, start_time_secs):
    dates = []
    num_days = end_date_index - start_date_index + 1
    for di in range(num_days):
        dates.append(data_dates[start_date_index + di])
    instruments = []
    instrument_map = {}

    polling_instrument_set(data_path, dates, instruments, instrument_map)
    num_insts = len(instruments)
    for f in data_fields:
        data = np.zeros((num_days, num_insts), dtype=np.float32)
        f.append(data)

    extra_date = -1
    if (start_time_secs > 0):
        extra_date = data_dates[end_date_index+1]
    load_and_process_daily_data(data_fields, data_path, instruments,
                                instrument_map, dates, start_time_secs, 0, extra_date)

    return dates, instruments, instrument_map


def load_and_update_data(data_dir, data_fields, data_path, data_dates, end_date_index, start_time_secs):
    dates = BUtils.load_array_from_text_file(data_dir + "/dates", int)
    instruments = BUtils.load_text_file(data_dir + "/tickers")
    instrument_map = {}
    num_insts = len(instruments)
    for ii in range(num_insts):
        instrument_map[instruments[ii]] = ii

    num_days = len(dates)
    for f in data_fields:
        f.append(BDataUtils.load_np_array_data(
            data_dir, f[0], np.float32, (num_days, num_insts)))

    last_date = dates[num_days-1]
    di = bisect.bisect_left(data_dates, last_date)
    if (data_dates[di] == last_date):
        di += 1
    for i in range(di, end_date_index+1):
        dates.append(data_dates[i])

    if (len(dates) == num_days):
        print(len(dates), num_days)
        return False, dates, instruments, instrument_map
    di_start = num_days
    num_days = len(dates)
    resize_data_fields(data_fields, num_days, di_start, num_insts, num_insts)
    extra_date = -1
    if (start_time_secs > 0):
        extra_date = data_dates[end_date_index+1]
    load_and_process_daily_data(data_fields, data_path, instruments,
                                instrument_map, dates, start_time_secs, di_start, extra_date)

    return True, dates, instruments, instrument_map


def build_data(xml_node, global_data):
    id, data_dir = BUtils.get_basic_attrs(xml_node, global_data)
    data_path = BUtils.format_path(
        BUtils.get_compulsory_attr(xml_node, "data_path", id))
    # data_period = BUtils.get_compulsory_attr(xml_node, "data_period", id)
    field_map = BUtils.get_compulsory_attr(xml_node, "field_map", id)

    data_fields = parse_field_map(field_map)

    sim_start_date = global_data["start_date"]
    sim_end_date = global_data["end_date"]
    back_days = global_data["back_days"]
    daily_start_time = global_data["daily_start_time"]
    start_time_secs = BUtils.time_to_seconds(daily_start_time)

    meta_info = str([field_map, data_path, daily_start_time])

    meta_lines = BDataUtils.load_meta_file(data_dir)

    data_dates = get_daily_data_dates_sorted(data_path)
    data_dates_limit = len(data_dates)-1
    if (daily_start_time > 0):
        data_dates_limit -= 1

    start_date_index = bisect.bisect_left(data_dates, sim_start_date)
    if (start_date_index < back_days):
        raise Exception("On date " + str(sim_start_date) +
                        ", there are not enough history data for back days " + str(back_days))

    if (start_date_index > data_dates_limit):
        raise Exception(
            "There is no base data on the start date " + str(sim_start_date))

    start_date_index -= back_days

    end_date_index = bisect.bisect_left(data_dates, sim_end_date)
    if (end_date_index > data_dates_limit):
        end_date_index = data_dates_limit

    if not check_meta_valid(meta_info, data_dates[start_date_index], meta_lines):
        print("build from scratch")
        dates, instruments, instrument_map = build_from_scratch(
            data_fields, data_path, data_dates, start_date_index, end_date_index, start_time_secs)
        random.seed()
        meta_lines = [meta_info, dates[0], random.randrange(0, 2000000000)]
        BUtils.create_dir(data_dir)
        BDataUtils.save_meta_file(data_dir, meta_lines)
        has_update = True
    else:
        has_update, dates, instruments, instrument_map = load_and_update_data(
            data_dir, data_fields, data_path, data_dates, end_date_index, start_time_secs)

    if (has_update):
        BUtils.save_text_file(data_dir + "/dates", dates)
        BUtils.save_text_file(data_dir + "/tickers", instruments)
        for f in data_fields:
            BDataUtils.save_np_array_data(data_dir, f[0], f[3])

    global_data["dates"] = dates
    global_data["tickers"] = instruments
    global_data["ticker_map"] = instrument_map
    for f in data_fields:
        global_data[f[0]] = f[3]
    global_data["data_version"] = int(meta_lines[2])
    start_di = bisect.bisect_left(dates, sim_start_date)
    end_di = bisect.bisect_left(dates, sim_end_date)
    if (end_di == len(dates)) or (dates[end_di] != sim_end_date):
        end_di -= 1
    global_data["start_sim_di"] = start_di
    global_data["end_sim_di"] = end_di

    # test_data(global_data)


def test_data(global_data):
    dates = global_data["dates"]
    instruments = global_data["tickers"]
    instrument_map = global_data["ticker_map"]
    close = global_data["close"]
    volume = global_data["volume"]

    print("Test base data")
    ii = instrument_map["BTCUSDT"]
    for di in range(len(dates)):
        print(dates[di], instruments[ii], close[di][ii], volume[di][ii])

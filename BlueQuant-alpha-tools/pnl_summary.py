import sys
import math
import pathlib
import os


class Stats:
    pass


def load_pnl_file(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    stats = []
    for line in lines:
        tokens = line.split(",")
        # print(tokens)
        # [self.dates[di], long_book, short_book, num_long, num_short, trade, pnl]
        n = len(tokens)
        if (n < 7):
            continue
        r = []
        r.append(int(tokens[0]))
        for i in range(1, 7):
            r.append(float(tokens[i]))
        stats.append(r)
    return stats


def load_pnl_files(foldername):
    files = os.listdir(foldername)
    sums = []
    for file in files:
        sums.append(load_pnl_file("pnl/" + file))
    return sums, files


def reset_stats(stats):
    stats.id = ''
    stats.num = 0
    stats.total_pnl = 0
    stats.total_pnl2 = 0
    stats.total_long = 0
    stats.total_short = 0
    stats.total_trade = 0
    stats.start = 0


def add_daily(daily, stats):
    stats.num += 1
    date, long, short, trade, pnl = daily[0], daily[1], daily[2], daily[5], daily[6]
    if (stats.start == 0):
        stats.start = date
    stats.end = date
    stats.total_pnl += pnl
    stats.total_pnl2 += pnl*pnl
    stats.total_long += long
    stats.total_short += short
    stats.total_trade += trade


def print_summary(stats):
    n = stats.num
    if (n == 0):
        return
    avg_pnl = stats.total_pnl / n
    avg_long = stats.total_long / n
    avg_short = stats.total_short / n
    avg_book = avg_long + avg_short
    avg_trade = stats.total_trade / n
    if avg_book != 0:
        ret = avg_pnl / avg_book * 356
        tvr = avg_trade / avg_book
    else:
        ret = 0
        tvr = 0
    var = (stats.total_pnl2 - n * avg_pnl * avg_pnl) / (n - 1)
    std = math.sqrt(var)
    if (std != 0):
        ir = avg_pnl / std
    else:
        ir = 0
    print("%30s %d-%d   %5.1f  %5.1f %8.1f  %5.1f %5.1f  %0.3f" % (stats.id, stats.start, stats.end,
          avg_long * 1e-3, avg_short * 1e-3, stats.total_pnl * 1e-3, tvr * 100, ret * 100, ir))


if (os.path.isdir(sys.argv[1])):
    src, ids = load_pnl_files(sys.argv[1])
    for i in range(len(src)):
        all_stats = Stats()
        period_stats = Stats()

        print("%30s %8s-%8s   %5s  %5s %8s  %5s %5s  %5s" %
              ("ALPHA ID", "START", "END", "LONG", "SHORT", "PNL", "TVR", "RET", "IR"))
        reset_stats(all_stats)
        reset_stats(period_stats)
        all_stats.id = ids[i]
        period_stats.id = ids[i]
        date_gap_threshold = 8000
        for daily in src[i]:
            add_daily(daily, all_stats)
            if ((period_stats.num > 0) and (daily[0] > period_stats.end + date_gap_threshold)):
                print_summary(period_stats)
                reset_stats(period_stats)
            add_daily(daily, period_stats)

        print_summary(period_stats)
        print()
        print_summary(all_stats)
        print("----------------------------------------------------------------------------------------------")
else:
    data = load_pnl_file(sys.argv[1])
    all_stats = Stats()
    period_stats = Stats()

    print("%30s %8s-%8s   %5s  %5s %8s  %5s %5s  %5s" %
          ("ALPHA ID", "START", "END", "LONG", "SHORT", "PNL", "TVR", "RET", "IR"))
    reset_stats(all_stats)
    reset_stats(period_stats)
    date_gap_threshold = 8000
    for daily in data:
        add_daily(daily, all_stats)
        if ((period_stats.num > 0) and (daily[0] > period_stats.end + date_gap_threshold)):
            print_summary(period_stats)
            reset_stats(period_stats)
        add_daily(daily, period_stats)

    print_summary(period_stats)
    print()
    print_summary(all_stats)
    print("----------------------------------------------------------------------------------------------")

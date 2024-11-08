import matplotlib
import matplotlib.pyplot as plt
import datetime
import matplotlib.dates
import numpy as np
import csv
import sys


def load_pnl_file(filename):
    with open(filename) as f:
        lines = f.read().splitlines()
    dates = []
    pnls = []
    for line in lines:
        tokens = line.split(",")
        # print(tokens)
        n = len(tokens)
        if (n < 7):
            continue
        dates.append(int(tokens[0]))
        pnls.append(float(tokens[6]))
    return dates, pnls


def cummulative_pnls(pnls):
    size = len(pnls)
    for i in range(1, size):
        pnls[i] = pnls[i-1] + pnls[i]
    # return pnls


def get_alpha_id(path):
    tokens = path.split("/")
    return tokens[len(tokens) - 1]


def merge_dates(all_dates):
    dates = []
    for list in all_dates:
        dates.extend(list)
    dates.sort()
    n = len(dates)
    m = 0
    for i in range(0, n):
        if ((i == 0) or (dates[i] > dates[i-1])):
            dates[m] = dates[i]
            m += 1
    print(n, m)
    del dates[m:n]
    return dates


def sampling_date(dates, s_size):
    size = len(dates)
    if (size <= s_size):
        return dates
    m_pos = [0]
    for i in range(1, size):
        if (dates[i] - dates[i-1] > 40):
            m_pos.append(i)
    m_size = len(m_pos)
    if (m_pos[m_size-1] < size-1):
        m_pos.append(size-1)
        m_size += 1
    if (m_size >= s_size):
        s_dates = []
        for i in range(0, s_size):
            j = (i * (m_size-1)) // (s_size - 1)
            s_dates.append(dates[m_pos[j]])
        return s_dates
    s = s_size - m_size
    d = (size-1) // (s_size-1)
    r = -1
    while (True):
        cc = 0
        for i in range(0, m_size-1):
            cc += (m_pos[i+1] - m_pos[i] - 1) // d
        r = s - cc
        if (r >= 0):
            break
        d += 1
    k = m_size-2
    while (k >= 0):
        x = (m_pos[k+1] - m_pos[k] - 1)
        n1 = x // d
        n2 = x // (d-1)
        if (n2 - n1 > r):
            break
        r -= n2 - n1
        k = k - 1
    s_dates = []
    for i in range(0, m_size-1):
        length = m_pos[i+1] - m_pos[i]
        pos = m_pos[i]
        s_dates.append(dates[pos])
        if (length <= d):
            continue
        if (i == k):
            n = r + (length - 1) // d
        elif (i < k):
            n = (length - 1) // d
        else:
            n = (length - 1) // (d-1)
        q = (length) // (n+1)
        x = length - q * (n+1)
        for j in range(0, n):
            pos += q
            if (i < x):
                pos += 1
            s_dates.append(dates[pos])
    s_dates.append(dates[size-1])
    return s_dates


def check_sampling_date(dates):
    print("Sampling size", len(dates))
    n = len(dates)
    i = 0
    while (i < n):
        x = dates[i] // 100
        j = i+1
        while ((j < n) and (dates[j] // 100 == x)):
            j += 1
        print(dates[i], (j-i))
        i = j


def sampling_label_base(dates, max_size):
    size = len(dates)
    indices = [0]
    for i in range(1, size):
        if ((dates[i] - dates[i-1]) > 40):
            indices.append(i)
    n = len(indices)
    if (n <= max_size):
        return indices
    m = 0
    for i in range(0, n):
        r = dates[indices[i]] // 100
        r = (r % 100) % 3
        # print(dates[indices[i]], "->", r)
        if (r == 1):
            indices[m] = indices[i]
            m += 1
    # print(indices[0:m])
    if (m <= max_size):
        return indices[0:m]
    n = m
    m = 0
    for i in range(0, n):
        r = dates[indices[i]] // 100
        r = r % 100
        if (r == 1):
            indices[m] = indices[i]
            m += 1
    return indices[0:m]


def sampling_label(dates, max_size):
    indices = sampling_label_base(dates, max_size)
    if ((len(indices) > 1) and (indices[1] - indices[0] < len(dates) // (2*max_size))):
        del indices[0]
    return indices


def extract_plot_data(dates, a_dates, a_pnls):
    indices = []
    pnls = []
    j = 0
    a_size = len(a_dates)
    for i in range(0, len(dates)):
        while ((j < a_size) and (a_dates[j] < dates[i])):
            j += 1
        if ((j < a_size) and (dates[i] == a_dates[j])):
            indices.append(i)
            pnls.append(a_pnls[j])
    return indices, pnls


all_dates = []
all_pnls = []
alpha_ids = []
n = len(sys.argv) - 1
for i in range(1, n+1):
    path = sys.argv[i]
    dates, pnls = load_pnl_file(path)
    cummulative_pnls(pnls)
    alpha_id = get_alpha_id(path)
    all_dates.append(dates)
    all_pnls.append(pnls)
    alpha_ids.append(alpha_id)
    # print(len(dates))

dates = merge_dates(all_dates)
dates = sampling_date(dates, 250)  # sampling size = 250
show_indices = sampling_label(dates, 15)  # 15 date label points
show_labels = []
for index in show_indices:
    show_labels.append(dates[index])
colors = ["r", "g", "b", "c", "m", "y"]
fig, ax = plt.subplots()
for i in range(0, n):
    x, y = extract_plot_data(dates, all_dates[i], all_pnls[i])
    ax.plot(x, y, colors[i], label=alpha_ids[i])
    # print(y)
plt.xlim(0, len(dates))
plt.xticks(show_indices, (show_labels), rotation=45)

ax.set(xlabel='date', ylabel='pnl')

ax.grid(True)
# plt.legend()
# fig.savefig("charts/" + ticker + ".png", bbox_inches='tight')
title = "PNL plot"
for id in alpha_ids:
    if (len(title) > 0):
        title += " "
    title += id
# fig.canvas.set_window_title(title)
plt.title(title)

plt.show()

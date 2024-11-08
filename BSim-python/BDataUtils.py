import math
import numpy as np
import os
import BUtils


def load_meta_file(data_dir):
    return BUtils.load_text_file(data_dir + "/metafile")


def save_meta_file(data_dir, meta_lines):
    return BUtils.save_text_file(data_dir + "/metafile", meta_lines)


def get_reusable_data_shape(data_dir, meta_info):
    meta_lines = load_meta_file(data_dir)
    if (len(meta_lines) >= 3) and (meta_info == meta_lines[0]):
        return (int(meta_lines[1]), int(meta_lines[2]))
    return (0, 0)


def resize_np_matrix(matrix, new_r, new_c, default_value=0):
    new_matrix = np.zeros((new_r, new_c), dtype=matrix.dtype)
    old_r = matrix.shape[0]
    old_c = matrix.shape[1]

    for c in range(old_c):
        for r in range(old_r):
            new_matrix[r][c] = matrix[r][c]

    for c in range(old_c, new_c):
        for r in range(old_r):
            new_matrix[r][c] = default_value

    return new_matrix


def load_np_array_data(data_dir, id, type, shape):
    # print("shape =", shape)
    data = np.fromfile(data_dir + "/" + id, dtype=type,
                       count=-1, sep="").reshape(shape)
    print("Loaded array", id)
    return data


def save_np_array_data(data_dir, id, data):
    data.tofile(data_dir + "/" + id, "")
    print("Saved array", id)


def save_all_register_data(data_dir, data_infos):
    for info in data_infos:
        save_np_array_data(data_dir, info[0], info[1])


def add_np_array_data(data_dir, id, type, old_shape, new_shape, default_value):
    if (old_shape[0] == 0):
        return np.zeros(new_shape, dtype=type)
    data = load_np_array_data(data_dir, id, type, old_shape)
    if (old_shape == new_shape):
        return data
    new_data = np.zeros(new_shape, dtype=type)
    d = len(new_shape)
    if (d == 1):
        for i in range(old_shape[0]):
            new_data[i] = data[i]
    elif (d == 2):
        for i in range(old_shape[0]):
            for j in range(old_shape[1]):
                new_data[i][j] = data[i][j]
            for j in range(old_shape[1], new_shape[1]):
                new_shape[i][j] = default_value
    return new_data


def register_data(global_data, data_infos, data_dir, id, type, old_shape, new_shape, default_value):
    data = add_np_array_data(
        data_dir, id, type, old_shape, new_shape, default_value)
    global_data[id] = data
    data_infos.append([id, data])
    return data


def patch_data(data):
    s = -1
    for i in range(len(data)):
        for j in range(len(data[0])):
            if not math.isnan(data[i][j]):
                if s != -1:
                    diff = data[i][j] - data[i][s - 1]
                    diff /= j-s + 2
                    if (data[i][s - 1] == 0):
                        diff = 0
                    for k in range(s, j):
                        data[i][k] = data[i][k - 1] + diff
                    s = -1
                continue
            if j == 0:
                data[i][j] = 0
            else:
                if (s == -1):
                    s = j
    if s != -1:
        for j in range(len(data)):
            for i in range(s, len(data[0])):
                data[j][i] = data[j][i-1]
    return data

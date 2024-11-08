import math


def sort2nd(x):
    return x[1]


def rank(arr):
    temp_arr = []
    for i in range(len(arr)):
        temp_arr.append([i, arr[i]])
    temp_arr.sort(key=sort2nd, reverse=True)
    temp = [0] * len(arr)
    for i in range(len(arr)):
        temp[temp_arr[i][0]] = i + 1
    return temp


def delay(x, d):
    return x[len(x) - 1 - d]


def correlation(x, y, d):
    '''return the correlation using the pearson \
    product-moment correlation method using today\'s price, set curr to today's\
    - 1 to use yesterday\'s price '''
    sx = 0
    sy = 0
    sxy = 0
    sxx = 0
    syy = 0
    curr = len(x) - 1
    if len(x) < d:
        raise Exception("Not enough data")
    for i in range(d):
        sx += x[curr-i]
        sy += y[curr-i]
        sxy += x[curr-i] * y[curr-i]
        sxx += x[curr-i] * x[curr-i]
        syy += y[curr-i] * y[curr-i]
    corr = (d * sxy - sx * sy) / \
        math.sqrt((d * sxx - sx*sx) * (d * syy - sy * sy))
    return corr


def covarience(x, y, d):

    medx, medy, s = 0
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough data")
    for i in range(d):
        medx += x[curr-i]
        medy += y[curr-i]
    for i in range(d):
        s += (x[curr - i] - medx) * (y[curr - y] - medy)
    s /= (d - 1)
    return s


def scale(arr, a):
    abs_sum = 0
    scaled = [0]*len(arr)
    for i in range(arr):
        abs_sum += abs(arr[i])
    for i in range(arr):
        scaled[i] = arr[i] * a / abs_sum
    return scaled


def delta(x, d):
    curr = len(x) - 1
    if curr < d:
        raise Exception(
            "Not enough data")

    return (x[curr] - x[curr - d])


def decay_linear(x, d):
    curr = len(x) - 1
    if curr < d:
        raise Exception(
            "Not enough data")
    a = [0] * d
    sum_of_weight = d * (d-1)/2
    temp = 0
    for i in range(d):
        for j in range(d):
            a[i] += x[curr - d + 1 - j] * (d - j)
        a[i] = a[i]/sum_of_weight
        temp += a[i]
    for i in range(d):
        a[i] /= temp
    return a


# neutralizer but is neutralized by industry
def indneutralize(x):
    return 0


def ts_min(x, d):
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days for delay of" + d + " days")

    min = x[curr]
    for i in range(d):
        if min > x[curr - i]:
            min = x[curr - i]
    return min


def ts_max(x, d):
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days for delay of" + d + " days")
    curr -= 1
    max = x[curr]
    for i in range(d):
        if max < x[curr - i]:
            max = x[curr-i]
    return max


def ts_argmin(x, d):
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days for delay of" + d + " days")
    idx = 0
    min = x[curr]
    for i in range(d):
        if min > x[curr - i]:
            min = x[curr-i]
            idx = curr - i
    return idx


def ts_argmax(x, d):
    curr = len(x) - 1
    if curr - 1 < d:
        raise Exception("Not enough days for delay of" + d + " days")
    idx = 0
    max = x[curr]
    for i in range(d):
        if max < x[curr - i]:
            max = x[curr-i]
            idx = curr - i
    return idx


def ts_rank(x, d):
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days for delay of" + d + " days")
    return rank(x[curr - d + 1:])


def sum(x, d):
    s = 0
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days for delay of" + d + " days")
    for i in range(d):
        s += x[curr-i]
    return s


def product(x, d):
    s = 1
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days for delay of" + d + " days")
    for i in range(d):
        s *= x[curr-i]
    return s


def stddev(x, d):
    avg = sum(x, d)/d
    curr = len(x) - 1
    if curr < d:
        raise Exception("Not enough days")
    s = 0
    for i in range(d):
        s += pow(x[curr - i] - avg, 2)
    s /= d
    return math.sqrt(s)

import math
import datetime
import os

EPS = 1e-6


def print_xml_node(node, n):
    for i in range(n):
        print("\t", end="")
    print(node.tag, node.attrib)
    for child in node:
        print_xml_node(child, n+1)


def print_xml_doc(root):
    node = root.find("Processors")
    print(node.tag)

    if (node is None):
        return
    for child in node:
        print_xml_node(child, 1)


def get_compulsory_attr(xml_node, key, context):
    value = xml_node.get(key, None)
    if (value is None):
        raise Exception(context + ": Attribute " + key + " not found in XML!")
    return value


def format_path(path):
    if (path.endswith("/")):
        path = path[:-1]
    return path


def get_basic_attrs(xml_node, global_data):
    id = xml_node.get("id", None)
    if (id is None):
        raise Exception("Module has no ID!" + xml_node.attrib)
    id_set = global_data["id_set"]
    if (id in id_set):
        raise Exception("Duplicate id" + id)
    id_set.add(id)

    data_dir = format_path(xml_node.get("data_dir", global_data["data_dir"]))
    data_dir = data_dir + "/" + id
    return id, data_dir


def load_text_file(filename):
    lines = []
    try:
        f = open(filename)
        for line in f.readlines():
            n = len(line)
            if (n == 0):
                continue
            if (line[n-1] == '\n'):
                line = line[0:n-1]
            if (len(line) == 0):
                continue
            lines.append(line)
        f.close()
    except:
        pass
    return lines


def load_array_from_text_file(filename, type):
    lines = load_text_file(filename)
    a = []
    for line in lines:
        a.append(type(line))
    return a


def save_text_file(filename, lines):
    try:
        f = open(filename, "w")
        for line in lines:
            f.write(str(line))
            f.write("\n")
        f.close()
        print("Saved", filename, len(lines))
    except:
        pass
    return lines


def get_year_month_day(yyyymmdd):
    yyyymm = yyyymmdd // 100
    yyyy = yyyymm // 100
    mm = yyyymm - yyyy * 100
    dd = yyyymmdd - yyyymm * 100
    return yyyy, mm, dd


def get_date_timestamp(yyyymmdd):
    y, m, d = get_year_month_day(yyyymmdd)
    dt = datetime.datetime(y, m, d, tzinfo=datetime.timezone.utc)
    return int(datetime.datetime.timestamp(dt))


def time_to_seconds(hhmmss):
    h, m, s = get_year_month_day(hhmmss)
    return (h*60 + m) + s


def int_to_str(n, digits):
    s = str(n)
    while len(s) < digits:
        s = "0" + s
    return s


def create_dir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


class BDict:
    def __init__(self):
        self.__pairs = {}

    def __getitem__(self, key):
        return self.__pairs[key]

    # once a key has been set, any later write on that key will be forbidden
    def __setitem__(self, key, value):
        if (key in self.__pairs):
            print("Cannot set key", key, "when it has already been set!")
            return
        self.__pairs[key] = value

    def __str__(self):
        return str(self.__pairs)


def scale_to_booksize(alpha, booksize):
    size = len(alpha)
    for ii in range(size):
        if (math.isnan(alpha[ii])):
            alpha[ii] = 0.0
    if (booksize < EPS):
        return
    total = 0
    for ii in range(size):
        total += abs(alpha[ii])
    if (total < EPS):
        return
    scale = booksize / total
    for ii in range(size):
        alpha[ii] *= scale
    # print(alpha)

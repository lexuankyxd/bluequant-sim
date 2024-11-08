import math


class Transform:
    def create(self, global_data, xml_node):
        # self.__global_data = global_data
        self.mode = int(xml_node.get("mode", 0))

    def transform(self, alpha):
        n = 0
        sum = 0
        size = len(alpha)
        for ii in range(size):
            if (math.isnan(alpha[ii])):
                continue
            sum += alpha[ii]
            n += 1
        if (n == 0):
            return
        mean = sum / n
        for ii in range(size):
            if (not math.isnan(alpha[ii])):
                alpha[ii] -= mean

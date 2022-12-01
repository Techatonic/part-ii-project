import heapq


class PriorityQueue:
    def __init__(self, variables_dict=None):
        if variables_dict is None:
            variables_dict = []
        self.queue = [QueueNode(variable, variables_dict[variable]) for variable in variables_dict]
        heapq.heapify(self.queue)

    def add(self, variable_name, domain):
        self.queue.append(QueueNode(variable_name, domain))
        heapq.heapify(self.queue)

    def remove(self):
        return heapq.heappop(self.queue)


class QueueNode:
    def __init__(self, variable, domain):
        self.variable = variable
        self.domain = domain

    def __lt__(self, other):
        return len(self.domain) < len(other.domain)

import heapq

from src.events.event import Event


class PriorityQueue:
    def __init__(self, variables_dict=None):
        if variables_dict is None:
            variables_dict = {}
        self.variables = [QueueNode(variable, variables_dict[variable]) for variable in variables_dict]
        heapq.heapify(self.variables)

    def add(self, variable_name, domain):
        self.variables.append(QueueNode(variable_name, domain))
        heapq.heapify(self.variables)

    def pop(self):
        return heapq.heappop(self.variables)


class QueueNode:
    def __init__(self, variable, domain: list[Event]):
        self.variable = variable
        self.domain = domain

    def __lt__(self, other):
        return len(self.domain) < len(other.domain)

    def __eq__(self, other):
        return self.variable == other.variable and self.domain == other.domain

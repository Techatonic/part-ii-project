import heapq


class PriorityQueue:
    def __init__(self, comparator, variables_dict: dict[str, any] | None = None) -> None:
        if variables_dict is None:
            variables_dict = {}
        self.comparator = comparator
        self.variables = [QueueNode(variable, variables_dict[variable], comparator) for variable in variables_dict]
        heapq.heapify(self.variables)

    def add(self, variable_name: str, domain) -> None:
        self.variables.append(QueueNode(variable_name, domain, self.comparator))
        heapq.heapify(self.variables)

    def pop(self):
        return heapq.heappop(self.variables)

    def set(self, variables) -> None:
        self.variables = variables
        heapq.heapify(self.variables)

    def __copy__(self):
        new_queue = PriorityQueue(self.comparator)
        new_queue.set([QueueNode(variable.variable, variable.domain, self.comparator) for variable in self.variables])
        return new_queue


class QueueNode:
    def __init__(self, variable: str, domain, comparator) -> None:
        self.variable = variable
        self.domain = domain
        self.comparator = comparator

    def __lt__(self, other) -> bool:
        return self.comparator(self, other)

    def __eq__(self, other) -> bool:
        return self.variable == other.variable and self.domain == other.domain

import heapq

from src.events.event import Event


class PriorityQueue:
    def __init__(self, variables_dict: dict[str, list[Event]] | None = None) -> None:
        if variables_dict is None:
            variables_dict = {}
        self.variables = [QueueNode(variable, variables_dict[variable]) for variable in variables_dict]
        heapq.heapify(self.variables)

    def add(self, variable_name: str, domain: list[Event]) -> None:
        self.variables.append(QueueNode(variable_name, domain))
        heapq.heapify(self.variables)

    def pop(self):
        return heapq.heappop(self.variables)

    def set(self, variables) -> None:
        self.variables = variables
        heapq.heapify(self.variables)

    def __copy__(self):
        new_queue = PriorityQueue()
        new_queue.set([QueueNode(variable.variable, variable.domain) for variable in self.variables])
        return new_queue


class QueueNode:
    def __init__(self, variable: str, domain: list[Event]) -> None:
        self.variable = variable
        self.domain = domain

    def __lt__(self, other) -> bool:
        # return len(self.domain) < len(other.domain)
        return self.domain[0].round.round_index > other.domain[0].round.round_index or self.domain[
            0].round.round_index == other.domain[0].round.round_index and len(self.domain) < len(other.domain)

    def __eq__(self, other) -> bool:
        return self.variable == other.variable and self.domain == other.domain

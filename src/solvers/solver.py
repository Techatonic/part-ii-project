from abc import ABC, abstractmethod

from src.events.event import Event


class Solver(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def add_variable(self, new_var: str, domain: list[Event]):
        pass

    @abstractmethod
    def add_constraint(self, function_name, variables=None, sport=None):
        pass

    @abstractmethod
    def solve(self):
        pass

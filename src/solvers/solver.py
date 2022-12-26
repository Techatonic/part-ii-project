from abc import ABC, abstractmethod

from src.events.event import Event
from src.sports.sport import Sport


class Solver(ABC):
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        pass

    @abstractmethod
    def add_constraint(self, function_name:str, variables:list[str] | None=None, sport:Sport | None=None) -> None:
        pass

    @abstractmethod
    def solve(self) -> dict[str, Event]|None:
        pass

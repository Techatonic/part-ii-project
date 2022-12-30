from abc import ABC, abstractmethod

from src.events.event import Event
from src.sports.sport import Sport


class Solver(ABC):
    @abstractmethod
    def __init__(self, forward_check) -> None:
        self.data = {}

    @abstractmethod
    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        pass

    @abstractmethod
    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        pass

    def add_optional_constraint(self, function_name: str, sport: Sport | None, params: dict = None):
        pass

    @abstractmethod
    def solve(self) -> dict[str, Event] | None:
        pass

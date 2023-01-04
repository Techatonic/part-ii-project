from abc import ABC, abstractmethod
from enum import Enum

from src.events.event import Event
from src.sports.sport import Sport


class SolverType(Enum):
    PYTHON_CONSTRAINT_SOLVER = 1,
    CUSTOMISED_SOLVER = 2,
    CSOP_SOLVER = 3


class Solver(ABC):
    @abstractmethod
    def __init__(self, data, forward_check) -> None:
        self.data = data
        self.forward_check = forward_check

    @abstractmethod
    def add_variable(self, new_var: str, domain) -> None:
        pass

    @abstractmethod
    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        pass

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params: dict = None):
        pass

    @abstractmethod
    def solve(self):
        pass

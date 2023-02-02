from abc import ABC, abstractmethod
from enum import Enum
from typing import Type

from src.schedulers.solvers.solver import Solver
from src.sports.sport import Sport


class SchedulerType(Enum):
    CSP_SCHEDULER = 1,
    CSOP_SCHEDULER = 2,


class Scheduler(ABC):
    @abstractmethod
    def __init__(self, solver: Type[Solver], sports: dict[str, Sport], data: dict, forward_check: bool):
        self.solver = solver
        self.sports = sports
        self.data = data
        self.forward_check = forward_check

    @abstractmethod
    def schedule_events(self):
        pass

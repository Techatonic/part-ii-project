from src.constraints.constraint import get_constraint_from_string
from src.events.event import Event
from src.solvers.solver import Solver
from constraint import Problem, BacktrackingSolver

from src.sports.sport import Sport


class ModuleSolver(Solver):
    def __init__(self, data, forward_check: bool) -> None:
        self.csp: Problem = Problem(BacktrackingSolver(forward_check))
        self.data = data

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        self.csp.addVariable(new_var, domain)

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        constraint_function = get_constraint_from_string(function_name)
        if variables is None:
            self.csp.addConstraint(constraint_function.function)
        else:
            self.csp.addConstraint(constraint_function.function, variables)

    def solve(self) -> dict[str, Event] | None:
        return self.csp.getSolution()

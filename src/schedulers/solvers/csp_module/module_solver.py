from src.constraints.constraint import get_constraint_from_string, ConstraintType
from src.events.event import Event
from src.schedulers.solvers.solver import Solver
from constraint import Problem, BacktrackingSolver

from src.sports.sport import Sport


class ModuleSolver(Solver):
    def __init__(self, data, forward_check: bool) -> None:
        self.csp: Problem = Problem(BacktrackingSolver(forward_check))
        self.data = data
        self.variables = {}

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        self.csp.addVariable(new_var, domain)
        self.variables[new_var] = domain

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        constraint_function = get_constraint_from_string(function_name)

        if constraint_function.constraint_type == ConstraintType.UNARY:
            for event_id in self.variables:
                self.csp.addConstraint(constraint_function.function, [event_id])
        elif constraint_function.constraint_type == ConstraintType.BINARY:
            for event_id_1 in range(len(self.variables.keys())):
                for event_id_2 in range(event_id_1 + 1, len(self.variables.keys())):
                    self.csp.addConstraint(constraint_function.function, [event_id_1, event_id_2])
        else:
            self.csp.addConstraint(constraint_function.function)

    def solve(self) -> dict[str, Event] | None:
        return self.csp.getSolution()

import copy
from functools import partial

from src.constraints.constraint import get_constraint_from_string, ConstraintType
from src.constraints.constraint_checker import single_constraint_check
from src.constraints.optional_constraints import get_inequality_operator_from_input, get_optional_constraint_from_string
from src.events.event import Event
from src.schedulers.solver import Solver
from constraint import Problem, BacktrackingSolver

from src.sports.sport import Sport


class ModuleSolver(Solver):
    def __init__(self, data, forward_check: bool) -> None:
        self.csp: Problem = Problem(BacktrackingSolver(forward_check))
        self.data = data
        self.variables = {}
        self.constraints = []
        self.optional_constraints = []

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        self.csp.addVariable(new_var, domain)
        self.variables[new_var] = domain

    def get_variables(self) -> dict:
        return self.variables

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        constraint = get_constraint_from_string(function_name)(variables, sport, params)

        if constraint.get_constraint_type() == ConstraintType.UNARY:
            for event_id in self.variables:
                self.csp.addConstraint(partial(single_constraint_check, constraint), [event_id])
        elif constraint.get_constraint_type() == ConstraintType.BINARY:
            for event_id_1 in range(len(self.variables.keys())):
                for event_id_2 in range(event_id_1 + 1, len(self.variables.keys())):
                    self.csp.addConstraint(partial(single_constraint_check, constraint), [event_id_1, event_id_2])
        else:
            self.csp.addConstraint(partial(single_constraint_check, constraint))

        self.constraints.append(constraint)

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params: object = None):
        params_copy = copy.deepcopy(params)
        if params_copy is None:
            params_copy = {}
        if not ("weight" in params_copy):
            params_copy["weight"] = 1
        if "inequality" in params_copy:
            params_copy["inequality"] = get_inequality_operator_from_input(params_copy["inequality"])

        constraint = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(constraint(None, sport, params_copy))

    def solve(self) -> dict[str, Event] | None:
        return self.csp.getSolution()

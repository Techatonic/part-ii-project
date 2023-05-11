import copy
from typing import Type

from src.constraints.constraint import Constraint, get_constraint_from_string, NoLaterRoundsBeforeEarlierRounds
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_inequality_operator_from_input, get_optional_constraint_from_string
from src.helper.handle_error import handle_error

from src.events.event import Event
from src.helper.ac3 import ac3
from src.helper.helper import copy_assignments
from src.helper.priority_queue import PriorityQueue
from src.sports.sport import Sport


class CSPSolver:
    def __init__(self, data, forward_check=False) -> None:
        self.queue = PriorityQueue(data["comparator"])
        self.data = data
        self.constraints = []
        self.optional_constraints = []
        self.forward_check = forward_check

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        if new_var in [variable.variable for variable in self.queue.variables]:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def get_variables(self) -> dict:
        variables = {}
        for variable in self.queue.variables:
            variables[variable.variable] = variable.domain
        return variables

    def add_constraint(self, class_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        class_ref = get_constraint_from_string(class_name)
        self.constraints.append(class_ref(variables, sport, copy.deepcopy(params)))

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
        # Add all events to constraints for all events
        self.constraints = self.__add_all_events_to_constraints()

        if self.forward_check:
            valid, new_queue = ac3(self.queue, self.constraints)
            if not valid:
                return None
            self.queue.set(new_queue.variables)

        result = self.__solve_variable({}, self.queue, 0)
        return result

    def __add_all_events_to_constraints(self) -> list[Constraint]:
        events = [variable.variable for variable in self.queue.variables]
        for constraint in range(len(self.constraints)):
            if self.constraints[constraint].get_variables() is not None:
                continue
            self.constraints[constraint].set_variables(events)
        return self.constraints

    def __solve_variable(self, assignments, queue: PriorityQueue, depth=0) -> dict[str, Event] | None:
        assignments: dict[str, Event] = copy_assignments(assignments)
        queue = queue.__copy__()

        while len(queue.variables) > 0:
            variable = queue.pop()

            for option in variable.domain:
                assignments[variable.variable] = option

                # Only need to test constraints involving the variable
                constraints_to_check = [constraint for constraint in self.constraints if
                                        variable.variable in constraint.get_variables()]
                satisfies_all_constraints = self.__test_constraints(assignments, constraints_to_check)
                if satisfies_all_constraints:
                    if self.forward_check:
                        valid, new_queue = ac3(queue, self.constraints)
                        if not valid:
                            continue
                        queue.set(new_queue.variables)

                    result = self.__solve_variable(assignments, queue, depth + 1)
                    if result is not None:
                        return result
            return None  # There is no valid assignment for this variable

        return assignments  # We have a valid assignment, return it

    def __test_constraints(self, assignments, constraints: list[Type[Constraint]]) -> bool:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(constraint, assignments)
        return len(conflicts) == 0

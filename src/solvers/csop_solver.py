from src.constraints.constraint import Constraint, get_constraint_from_string
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_optional_constraint_from_string
from src.error_handling.handle_error import handle_error

from src.events.event import Event
from src.helper.ac3 import ac3
from src.helper.helper import copy_assignments
from src.helper.priority_queue import PriorityQueue
from src.sports.sport import Sport


class CSOPSolver:
    def __init__(self, forward_check=False) -> None:
        self.queue = PriorityQueue()

        self.constraints: list[Constraint] = []
        self.optional_constraints: list[Constraint] = []
        self.forward_check: bool = forward_check
        self.data = {}

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        if new_var in [variable.variable for variable in self.queue.variables]:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: object = None) -> None:
        function = get_constraint_from_string(function_name)
        self.constraints.append(Constraint(function, variables, sport, params))

    def add_optional_constraint(self, function_name: str, sport: Sport | None, params: dict = None):
        function = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(Constraint(function, None, sport, params))

    # def add_data(self, key, value):
    #     self.data[key] = value
    #
    # def append_to_data_list(self, key, value_to_add):
    #     if not (key in self.data):
    #         handle_error(str(key) + " does not exist in data")
    #     if not (type(self.data[key]) == list):
    #         handle_error("Cannot append to element that is not a list")
    #     self.data[key].append(value_to_add)

    def __add_all_events_to_constraints(self) -> list[Constraint]:
        events = [variable.variable for variable in self.queue.variables]
        for constraint in range(len(self.constraints)):
            # print(self.constraints[constraint].variables)
            if self.constraints[constraint].variables is not None:
                continue
            self.constraints[constraint].variables = events
            # print()
            # print(self.constraints[constraint].variables)
        return self.constraints

    def solve(self) -> dict[str, Event] | None:
        # Add all events to constraints for all events
        self.constraints = self.__add_all_events_to_constraints()

        bound_data = BranchAndBound()
        self.__solve_variable({}, self.queue, bound_data)
        print(bound_data)
        return bound_data.best_solution

    def __solve_variable(self, assignments, queue: PriorityQueue, bound_data) -> None:
        assignments: dict[str, Event] = copy_assignments(assignments)
        queue = queue.__copy__()

        if len(queue.variables) == 0:
            heuristic_val = self.__heuristic(assignments)
            # print(heuristic_val)
            if heuristic_val > bound_data.bound or self.__is_acceptable_solution(assignments):
                bound_data.bound = heuristic_val
                bound_data.best_solution = assignments
                print(bound_data)
            else:
                print("Solution found - bound not good enough")
        elif len(assignments) == 0 or self.__heuristic(assignments) > bound_data.bound:
            variable = queue.pop()
            for option in variable.domain:
                assignments[variable.variable] = option

                if self.__test_constraints(assignments, self.constraints):
                    self.__solve_variable(assignments, queue, bound_data)
            return None

    def __is_acceptable_solution(self, assignments):
        events: list[Event] = list(assignments.values())
        for optional_constraint_heuristic in self.optional_constraints:
            if not (optional_constraint_heuristic.constraint.function(self, events)[0] >
                    optional_constraint_heuristic.params["aim"]):
                print("False")
                return False
        print("True")
        return True

    def __heuristic(self, assignments):
        events: list[Event] = list(assignments.values())
        return sum(
            optional_constraint_heuristic.constraint.function(self, events)[1] for optional_constraint_heuristic in
            self.optional_constraints)

    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        events: list[Event] = list(assignments.values())

        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(self, constraint.constraint, events, constraint.params)
        return len(conflicts) == 0


class BranchAndBound:
    def __init__(self):
        self.bound = -float('inf')
        self.best_solution = {}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            bound: {str(self.bound)},
        \n}}"""

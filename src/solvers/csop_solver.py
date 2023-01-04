from typing import Type

from src.constraints.constraint import Constraint, get_constraint_from_string, ConstraintType
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_optional_constraint_from_string
from src.error_handling.handle_error import handle_error

from src.events.event import Event
from src.helper.branch_and_bound import BranchAndBound
from src.helper.helper import copy_assignments
from src.helper.priority_queue import PriorityQueue
from src.sports.sport import Sport


class CSOPSolver:
    def __init__(self, data=None, forward_check=False) -> None:
        self.data = data if data is not None else {}

        self.queue = PriorityQueue(self.data["comparator"])
        self.constraints: list[Constraint] = []
        self.optional_constraints: list[Constraint] = []
        self.forward_check: bool = forward_check

    def add_variable(self, new_var: str, domain) -> None:
        if new_var in [variable.variable for variable in self.queue.variables]:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        function = get_constraint_from_string(function_name)
        self.constraints.append(Constraint(function, variables, sport, params))

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params=None):
        if params is None:
            params = {}
        if not ("weight" in params):
            params["weight"] = 1
        function = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(Constraint(function, None, sport, params))

    # def __add_all_events_to_constraints(self) -> list[Constraint]:
    #     events = [variable.variable for variable in self.queue.variables]
    #     for constraint in range(len(self.constraints)):
    #         if self.constraints[constraint].variables is not None:
    #             continue
    #         self.constraints[constraint].variables = events
    #     return self.constraints

    def solve(self):
        # Add all events to constraints for all events
        # TODO Check if it's ok to remove the line below
        # self.constraints = self.__add_all_events_to_constraints()

        self.__preprocess()

        bound_data = BranchAndBound(num_results=self.data["num_results_to_collect"])
        self.__solve_variable({}, self.queue, bound_data)
        print("Returning: ")
        return bound_data.best_solutions

    def __preprocess(self):
        unary_constraints = list(filter(lambda constraint: constraint.constraint_type == ConstraintType.UNARY,
                                        self.constraints))
        for unary_constraint in unary_constraints:
            for variable in self.queue.variables:
                for option in variable.domain:
                    if not unary_constraint.constraint.function(self, unary_constraint.params, option):
                        variable.domain.remove(option)
            self.constraints.remove(unary_constraint)

    def __solve_variable(self, assignments, queue: PriorityQueue, bound_data) -> Type[BranchAndBound] | None:
        variable_type = self.data["variable_type"]
        assignments: dict[str, variable_type] = copy_assignments(assignments)
        queue = queue.__copy__()
        # print(sum(len(variable.domain) for variable in queue.variables))
        if len(queue.variables) == 0:
            heuristic_val = self.__heuristic(assignments)
            if heuristic_val > bound_data.get_worst_bound():
                bound_data.update_bounds(heuristic_val, assignments)
                if bound_data.is_full() and self.__is_acceptable_solution(bound_data.get_worst_bound_solution()):
                    return bound_data
            else:
                print("Solution found - bound not good enough")
        elif len(assignments) == 0 or self.__heuristic(assignments) > bound_data.get_worst_bound():
            variable = queue.pop()
            for option in variable.domain:
                assignments[variable.variable] = option

                if self.__test_constraints(assignments, self.constraints):
                    result = self.__solve_variable(assignments, queue, bound_data)
                    if result is not None:
                        return result
            return None

    def __is_acceptable_solution(self, assignments):
        if assignments is None:
            return False
        for optional_constraint_heuristic in self.optional_constraints:
            if not (optional_constraint_heuristic.constraint.function(self, assignments)[0] >
                    optional_constraint_heuristic.params["acceptable"]):
                return False
        return True

    def __heuristic(self, assignments):
        normalising_factor = sum(optional_constraint_heuristic.params["weight"] for optional_constraint_heuristic in
                                 self.optional_constraints)
        # print(list(optional_constraint_heuristic.constraint.function(self, assignments)[1] *
        #           optional_constraint_heuristic.params["weight"] for optional_constraint_heuristic in
        #           self.optional_constraints))
        return sum(
            optional_constraint_heuristic.constraint.function(self, assignments)[1] *
            optional_constraint_heuristic.params["weight"] for optional_constraint_heuristic in
            self.optional_constraints) / normalising_factor

    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(self, constraint.constraint, assignments, constraint.params)
        return len(conflicts) == 0

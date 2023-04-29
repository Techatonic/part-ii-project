import copy
import time
from abc import ABC
from typing import Type

from src.constraints.constraint import Constraint, get_constraint_from_string, ConstraintType
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_optional_constraint_from_string, \
    get_inequality_operator_from_input, OptionalConstraint
from src.helper.handle_error import handle_error
from src.helper.best_solution import BestSolutions

from src.helper.helper import copy_assignments
from src.helper.priority_queue import PriorityQueue
from src.schedulers.solver import Solver
from src.sports.sport import Sport


class HeuristicBacktrackingSolver(Solver, ABC):
    def __init__(self, data=None, forward_check=False, sport=None) -> None:
        self.data = data if data is not None else {}

        self.sport = sport
        self.queue = PriorityQueue(self.data["comparator"])
        self.constraints: list[Constraint] = []
        self.optional_constraints: list[OptionalConstraint] = []
        self.forward_check: bool = forward_check

    def add_variable(self, new_var: str, domain) -> None:
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

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        constraint = get_constraint_from_string(function_name)
        self.constraints.append(constraint(variables, sport, copy.deepcopy(params)))

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params=None):
        params_copy = copy.deepcopy(params)
        if params_copy is None:
            params_copy = {}
        if not ("weight" in params_copy):
            params_copy["weight"] = 1
        if "inequality" in params_copy:
            params_copy["inequality"] = get_inequality_operator_from_input(params_copy["inequality"])

        constraint = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(constraint(None, sport, params_copy))
        # print(self.optional_constraints[0])

    def solve(self):
        self.data["start_time"] = time.time()
        self.__preprocess()

        best_solution = BestSolutions(self.data['num_results_to_collect'])
        self.__solve_variable({}, self.queue, best_solution)
        return best_solution.get_best_solutions()

    def __preprocess(self):
        unary_constraints = list(filter(lambda constraint: constraint.constraint_type == ConstraintType.UNARY,
                                        self.constraints))
        for unary_constraint in unary_constraints:
            for variable in self.queue.variables:
                for option in variable.domain:
                    if not unary_constraint.eval_constraint({option.id: option}):
                        variable.domain.remove(option)
            self.constraints.remove(unary_constraint)

    def __solve_variable(self, assignments, queue: PriorityQueue, best_solution: BestSolutions) -> Type[
                                                                                                       BestSolutions] | None | str:
        # TODO Maybe add this back - I'd say probably not
        # if time.time() - self.data["start_time"] > self.data["wait_time"]:
        #    raise TimeoutError
        variable_type = self.data["variable_type"]
        assignments: dict[str, variable_type] = copy_assignments(assignments)
        queue = queue.__copy__()
        # print(self.__heuristic(assignments) if len(assignments) > 0 else None)
        if len(queue.variables) == 0:
            heuristic_val = self.__heuristic(assignments)
            if heuristic_val > best_solution.get_worst_bound():
                best_solution.update_bounds(heuristic_val, assignments)
                # print("Improved solution found: ", best_solution)
            else:
                # print(heuristic_val, bound_data)
                # print("Solution found - bound not good enough")
                pass
        else:
            # print(len(assignments))
            variable = queue.pop()

            ###### Sort options by eval score #########
            domain_evals = []
            for option in variable.domain:
                assignments[variable.variable] = option
                domain_evals.append((option, self.__heuristic(assignments)))
                del assignments[variable.variable]

            variable.domain = filter(lambda x: x[1] > best_solution.get_worst_bound(),
                                     sorted(domain_evals, key=lambda x: x[1], reverse=True))
            variable.domain = [x[0] for x in variable.domain]
            ###########################################

            for option in variable.domain:
                assignments[variable.variable] = option

                if self.__test_constraints(assignments, self.constraints):
                    result = self.__solve_variable(assignments, queue, best_solution)
                    if result is not None:
                        return result
        # print("Returning none at end of function")

    def __heuristic(self, assignments):
        normalising_factor = sum(
            optional_constraint_heuristic.get_params()["weight"] for optional_constraint_heuristic in
            self.optional_constraints)
        if normalising_factor == 0:
            return 1
        if not self.__test_constraints(assignments, self.constraints):
            return 0
        return sum(
            optional_constraint_heuristic.eval_constraint(self, assignments)[1] *
            optional_constraint_heuristic.get_params()["weight"] for optional_constraint_heuristic in
            self.optional_constraints) / normalising_factor

    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        conflicts = []
        for constraint in constraints:
            # print(constraint)
            conflicts += constraint_check(constraint, assignments)
        return len(conflicts) == 0
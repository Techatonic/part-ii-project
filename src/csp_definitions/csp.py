from src.constraints.constraint_checker import constraint_check
from src.csp_definitions.constraint import Constraint
from src.error_handling.handle_error import handle_error
import copy

from src.helper.priority_queue import PriorityQueue


class CSPProblem:
    def __init__(self):
        self.queue = PriorityQueue()
        self.constraints = []

    def add_variable(self, new_var, domain):
        if new_var in self.queue.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def solve(self):
        result = self.solve_variable({}, self.queue)
        print(result)
        return result

    def solve_variable(self, assignments, queue):
        assignments = copy.deepcopy(assignments)
        queue = copy.deepcopy(queue)
        while len(queue.variables) > 0:
            variable = queue.pop()
            for option in variable.domain:
                assignments[variable.variable] = option

                # Only need to test constraints involving the variable
                # TODO Eventually we'll need to go through all constraints because of soft constraints
                constraints_to_check = [constraint for constraint in self.constraints if
                                        variable.variable_name in constraint.variables]
                satisfies_all_constraints = self.test_constraints(assignments, constraints_to_check)
                if satisfies_all_constraints:
                    # TODO Remove from all other domains affected
                    self.trim_queue(queue, {variable.variable: assignments[variable.variable]}, constraints_to_check)
                    # TODO Check is trim has successfully occurred in place
                    result = self.solve_variable(assignments, queue)
                    if result is not None:
                        return result

                del assignments[variable.variable]

            return None

        return assignments  # We have a valid assignment, return it

    def test_constraints(self, assignments, constraints: list[Constraint]):
        events = assignments.values()
        conflicts = []
        for constraint in constraints:
            is_general_constraint = constraint.sport is None

            if is_general_constraint:
                conflicts += constraint_check(constraint.function, events)
            else:
                events = filter(lambda event: event.sport == constraint.sport, events)
                conflicts += constraint_check(constraint.function, events)

        return len(conflicts) == 0

    def trim_queue(self, queue, most_recent_assignment, constraints):
        for variable in queue.variables:
            variable.domain = filter(
                lambda option: self.test_constraints(most_recent_assignment, constraints),
                variable.domain
            )

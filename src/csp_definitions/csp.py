from src.error_handling.handle_error import handle_error
import copy

from src.helper.priority_queue import PriorityQueue


class CSPProblem:
    def __init__(self):
        self.queue = PriorityQueue()
        self.constraints = []
        print(1)

    def add_variable(self, new_var, domain):
        if new_var in self.queue.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def solve(self):
        self.solve_variable({}, self.queue)

    def solve_variable(self, assignments, queue):
        assignments = copy.deepcopy(assignments)
        queue = copy.deepcopy(queue)
        while len(queue.variables) > 0:
            variable = queue.pop()
            for option in variable.domain:
                # Only need to test constraints involving
                # TODO Eventually we'll need to go through all constraints because of soft constraints
                assignments[variable.variable] = option
                satisfies_all_constraints = self.test_constraints(
                    assignments, [constraint for constraint in self.constraints if
                                  variable.variable_name in constraint.variables])
                if satisfies_all_constraints:
                    # TODO Remove from all other domains affected
                    self.solve_variable(assignments, queue)
                    # TODO Get return value and do correct thing in response
                else:
                    del assignments[variable.variable]

            return None

    def test_constraints(self, assignments, constraints):
        # TODO Implement this function
        return True

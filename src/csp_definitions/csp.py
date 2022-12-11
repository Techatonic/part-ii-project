from src.constraints.constraint import Constraint, get_constraint, ConstraintType
from src.constraints.constraint_checker import constraint_check
from src.error_handling.handle_error import handle_error
import copy
import heapq

from src.helper.priority_queue import PriorityQueue


class CSPProblem:
    def __init__(self):
        self.queue = PriorityQueue()
        # TODO think about reordering of constraints list so the hardest ones are evaluated first - should improve
        # TODO performance
        self.constraints = []

    def add_variable(self, new_var, domain):
        if new_var in self.queue.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def add_constraint(self, function_name, variables=None, sport=None):
        function = get_constraint(function_name)
        # print(function_name, function, variables, sport)
        self.constraints.append(Constraint(function, variables, sport))

    def solve(self):
        # Add all events to constraints for all events
        self.constraints = self.__add_all_events_to_constraints()

        result = self.__solve_variable({}, self.queue)
        # print(result)
        return result

    def __add_all_events_to_constraints(self):
        events = [variable.variable for variable in self.queue.variables]
        for constraint in range(len(self.constraints)):
            # print(self.constraints[constraint].variables)
            if self.constraints[constraint].variables is not None:
                continue
            self.constraints[constraint].variables = events
            print()
            print(self.constraints[constraint].variables)
        return self.constraints

    def __solve_variable(self, assignments, queue):
        assignments = copy.deepcopy(assignments)
        queue = copy.deepcopy(queue)
        while len(queue.variables) > 0:
            variable = queue.pop()
            for option in variable.domain:
                # print("\nNew option for: ", variable.variable)
                assignments[variable.variable] = option
                # print(assignments)

                # Only need to test constraints involving the variable
                # TODO Eventually we'll need to go through all constraints because of soft constraints
                constraints_to_check = [constraint for constraint in self.constraints if
                                        variable.variable in constraint.variables]
                satisfies_all_constraints = self.__test_constraints(assignments, constraints_to_check)
                if satisfies_all_constraints:
                    # TODO Remove from all other domains affected
                    # self.__trim_queue(queue, {variable.variable: assignments[variable.variable]}, constraints_to_check)
                    # TODO Check is trim has successfully occurred in place
                    result = self.__solve_variable(assignments, queue)
                    if result is not None:
                        return result

                del assignments[variable.variable]

            return None

        return assignments  # We have a valid assignment, return it

    def __test_constraints(self, assignments, constraints: list[Constraint]):
        events = list(assignments.values())
        conflicts = []
        for constraint in constraints:
            # print(constraint)
            is_general_constraint = constraint.sport is None
            if is_general_constraint:
                conflicts += constraint_check(constraint, events)
            else:
                events = list(filter(lambda event: event.sport == constraint.sport, events))
                conflicts += constraint_check(constraint, events)
        return len(conflicts) == 0

    def __trim_queue(self, queue, most_recent_assignment, constraints):
        for variable in queue.variables:
            variable.domain = list(filter(
                lambda option: self.__test_constraints(most_recent_assignment, constraints),
                variable.domain
            ))
        heapq.heapify(queue.variables)

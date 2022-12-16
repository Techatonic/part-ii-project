from src.constraints.constraint import Constraint, get_constraint, ConstraintType
from src.constraints.constraint_checker import constraint_check, valid_constraint_check
from src.error_handling.handle_error import handle_error
import copy
import heapq

from src.events.event import Event
from src.helper.priority_queue import PriorityQueue, QueueNode


class CSPProblem:
    def __init__(self):
        self.queue = PriorityQueue()
        # TODO think about reordering of constraints list so the hardest ones are evaluated first - should improve
        # TODO performance
        self.constraints = []

    def add_variable(self, new_var: str, domain: list[Event]):
        if new_var in [variable.variable for variable in self.queue.variables]:
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
        print(len(queue.variables))
        while len(queue.variables) > 0:
            variable = queue.pop()
            # print("Domain size: ", len(variable.domain))
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
                    # if self.__trim_queue(queue, {variable.variable: assignments[variable.variable]},
                    #                     constraints_to_check):
                    if self.__arc_consistency(queue, self.constraints):
                        # TODO Check is trim has successfully occurred in place
                        result = self.__solve_variable(assignments, queue)
                        if result is not None:
                            return result

                del assignments[variable.variable]

            return None
        print("Returning assignments")
        return assignments  # We have a valid assignment, return it

    # TODO This is basically the same as constraint_check in constraint_checker.py (except this is multiple constraints). Possibly merge them
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

    # def __trim_queue(self, queue, most_recent_assignment, constraints):
    #     """
    #     Trims domain of variables on the queue based on newest assignment
    #     Returns True if all variables still have possible assignments (i.e. len(domain) > 0)
    #     :param queue:
    #     :param most_recent_assignment:
    #     :param constraints:
    #     :return:
    #     """
    #     temp_queue = copy.deepcopy(queue)
    #     for variable in temp_queue.variables:
    #         print("Domain before: ", len(variable.domain))
    #         domain = []
    #         for option in variable.domain:
    #             assignments_to_check = most_recent_assignment
    #             assignments_to_check[variable.variable] = option
    #             if self.__test_constraints(assignments_to_check, constraints):
    #                 domain.append(domain)
    #
    #         variable.domain = domain
    #         if len(variable.domain) == 0:
    #             return False
    #
    #         print("Domain after: ", len(variable.domain))
    #
    #     # All domains have length > 0, so we know it's safe to trim the original queue
    #     queue.variables = temp_queue.variables
    #     heapq.heapify(queue.variables)
    #     return True

    def __arc_consistency(self, queue: PriorityQueue, constraints: list[Constraint]):
        queue = copy.deepcopy(queue)
        unary_constraints = list(
            filter(lambda constraint: constraint.constraint_type == ConstraintType.UNARY, constraints))
        binary_constraints = list(
            filter(lambda constraint: constraint.constraint_type == ConstraintType.BINARY, constraints))
        for variable in queue.variables:
            for unary_constraint in unary_constraints:
                variable.domain = [option for option in variable.domain if constraint_check(unary_constraint, [option])]

        worklist = [(x, y) for x in queue.variables for y in queue.variables if x != y]

        while len(worklist) > 0:
            (x, y) = worklist.pop(0)
            if self.__arc_reduce(x, y, binary_constraints):
                if len(x.domain) == 0:
                    print("AC-3 return false - ", x.variable)
                    return False
                # Add to worklist
                worklist += [(x, z) for z in queue.variables if z != y and z != x]
        return True

    def __arc_reduce(self, x, y, binary_constraints):
        made_change = False
        for x_option in x.domain:
            found_valid_pair = False
            for y_option in y.domain:
                if all(valid_constraint_check(binary_constraint, [x_option, y_option]) for binary_constraint in
                       binary_constraints):
                    found_valid_pair = True
                    break
            if not found_valid_pair:
                # print()
                # print(x_option)
                x.domain.remove(x_option)
                made_change = True
        return made_change

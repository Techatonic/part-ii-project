from src.constraints.constraint import Constraint, get_constraint_from_string
from src.constraints.constraint_checker import constraint_check
from src.error_handling.handle_error import handle_error

from src.events.event import Event
from src.helper.ac3 import ac3
from src.helper.helper import copy_assignments
from src.helper.priority_queue import PriorityQueue
from src.sports.sport import Sport


class CustomisedSolver:
    def __init__(self, forward_check=False) -> None:
        self.queue = PriorityQueue()

        self.constraints = []
        self.forward_check = forward_check

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        if new_var in [variable.variable for variable in self.queue.variables]:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.queue.add(new_var, domain)

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        function = get_constraint_from_string(function_name)
        # print(function_name, function, variables, sport)
        self.constraints.append(Constraint(function, variables, sport, params))

    def add_optional_constraint(self, function_name: str, sport: Sport | None, params: object = None):
        pass

    def solve(self) -> dict[str, Event] | None:
        # print(set(option.venue.name for option in self.queue.variables[0].domain))
        # print(set(option.day for option in self.queue.variables[0].domain))
        # print(set(option.start_time for option in self.queue.variables[0].domain))

        # Add all events to constraints for all events
        self.constraints = self.__add_all_events_to_constraints()

        result = self.__solve_variable({}, self.queue)
        # print(result)
        return result

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

    def __solve_variable(self, assignments, queue: PriorityQueue) -> dict[str, Event] | None:
        # print([[i.variable, len(i.domain)] for i in self.queue.variables])

        assignments: dict[str, Event] = copy_assignments(assignments)

        queue = queue.__copy__()
        # print(len(queue.variables))
        while len(queue.variables) > 0:
            variable = queue.pop()
            # print(sum(len(x.domain) for x in queue.variables) + len(variable.domain),
            # variable.domain[0].round.round_name)
            for option in variable.domain:
                assignments[variable.variable] = option

                # Only need to test constraints involving the variable
                # TODO Eventually we'll need to go through all constraints because of soft constraints
                constraints_to_check = [constraint for constraint in self.constraints if
                                        variable.variable in constraint.variables]
                satisfies_all_constraints = self.__test_constraints(assignments, constraints_to_check)
                if satisfies_all_constraints:
                    # Remove from all other domains affected
                    if (not self.forward_check) or ac3(queue, self.constraints):
                        result = self.__solve_variable(assignments, queue)
                        if result is not None:
                            return result

                # TODO Check if it's ok to remove the below line
                # del assignments[variable.variable]

            return None
        return assignments  # We have a valid assignment, return it

    # TODO This is basically the same as constraint_check in constraint_checker.py (except this is multiple constraints). Possibly merge them
    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        events: list[Event] = list(assignments.values())

        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(self, constraint.constraint, events, constraint.params)
        return len(conflicts) == 0

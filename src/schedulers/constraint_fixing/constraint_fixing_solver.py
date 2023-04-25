import copy
import time

from src.constraints.constraint import Constraint, get_constraint_from_string, constraints_list
from src.constraints.constraint_checker import constraint_check
from src.error_handling.handle_error import handle_error

from src.events.event import Event
from src.helper.helper import copy_assignments
from src.sports.sport import Sport


class ConstraintFixingSolver:
    def __init__(self, data, forward_check=False) -> None:
        self.queue = []
        self.data = data
        self.variables = {}
        self.constraints = []
        self.forward_check = forward_check
        self.assignments = self.data['assignments'][self.data['sport'].name]
        self.num_changes_allowed = self.data['num_changes_allowed']

    def add_variable(self, new_var: str, domain: list[Event]) -> None:
        if new_var in self.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.variables[new_var] = domain

    def get_variables(self) -> dict:
        return self.variables

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        constraint = get_constraint_from_string(function_name)
        self.constraints.append(constraint(variables, sport, copy.deepcopy(params)))

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params: object = None):
        pass

    def __add_all_events_to_constraints(self) -> list[Constraint]:
        events = [self.variables[variable] for variable in self.variables]
        for constraint in range(len(self.constraints)):
            if self.constraints[constraint].get_variables() is not None:
                continue
            self.constraints[constraint].set_variables(events)
        return self.constraints

    def solve(self) -> dict[str, Event] | None:
        # Add all events to constraints for all events
        self.constraints = self.__add_all_events_to_constraints()

        all_events = [value for variable in self.variables for value in self.variables[variable]]

        constraints_failed = self.__test_constraints(self.assignments, self.constraints)
        if constraints_failed == 0:
            return self.assignments

        queue = [(0, value, self.assignments, [], constraints_failed) for value in all_events]

        start = time.time()
        count = 0
        curr_depth = 0

        while len(queue) > 0:
            count += 1
            if queue[0][0] > curr_depth:
                queue = sorted(queue, key=lambda x: x[4])
                curr_depth += 1
            new_depth, changed_event, assignments, path, constraints_failed = queue.pop(0)
            assignments = copy_assignments(assignments)
            assignments[changed_event.id] = changed_event
            new_constraints_failed = self.__test_constraints(assignments, self.constraints)
            if new_constraints_failed == 0:
                print("Success by changing ", path + [changed_event.id], " at depth: ", new_depth + 1)
                print(f'{count} nodes checked in {time.time() - start} seconds')
                return assignments
            if new_constraints_failed > constraints_failed or new_depth == self.num_changes_allowed:
                continue
            for next_event in all_events:
                if not (next_event.id in (path + [changed_event.id])):
                    queue.append(
                        (new_depth + 1, next_event, assignments, path + [changed_event.id], new_constraints_failed))
        return None

    # TODO This is basically the same as constraint_check in constraint_checker.py (except this is multiple constraints). Possibly merge them
    def __test_constraints(self, assignments, constraints: list[Constraint]) -> int:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(constraint, assignments)
        return len(conflicts)

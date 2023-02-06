import copy

from src.constraints.constraint import Constraint, get_constraint_from_string, constraints_list
from src.constraints.constraint_checker import constraint_check
from src.error_handling.handle_error import handle_error

from src.events.event import Event
from src.helper.ac3 import ac3
from src.helper.helper import copy_assignments
from src.helper.priority_queue import PriorityQueue
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

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        function = get_constraint_from_string(function_name)
        self.constraints.append(Constraint(function, variables, sport, copy.deepcopy(params)))

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params: object = None):
        pass

    def __add_all_events_to_constraints(self) -> list[Constraint]:
        events = [self.variables[variable] for variable in self.variables]
        for constraint in range(len(self.constraints)):
            if self.constraints[constraint].variables is not None:
                continue
            self.constraints[constraint].variables = events
        return self.constraints

    def solve(self) -> dict[str, Event] | None:
        # Add all events to constraints for all events
        self.constraints = self.__add_all_events_to_constraints()

        all_events = [value for variable in self.variables for value in self.variables[variable]]
        queue = [(0, value, self.assignments, []) for value in all_events]

        if self.__test_constraints(self.assignments, self.constraints):
            return self.assignments

        while len(queue) > 0:
            depth, changed_event, assignments, path = queue.pop(0)
            assignments = copy_assignments(assignments)
            if depth >= self.num_changes_allowed:
                return None
            assignments[changed_event.event_id] = changed_event
            if self.__test_constraints(assignments, self.constraints):
                print("Success by changing ", path + [changed_event.event_id], " at depth: ", depth + 1)
                return assignments
            for next_event in all_events:
                if next_event.event_id != changed_event.event_id:
                    queue.append((depth + 1, next_event, assignments, path + [changed_event.event_id]))

        return None

    # TODO This is basically the same as constraint_check in constraint_checker.py (except this is multiple constraints). Possibly merge them
    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(constraint.constraint, assignments)
        return len(conflicts) == 0

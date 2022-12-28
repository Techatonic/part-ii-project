from src.constraints.constraint import ConstraintType, Constraint, constraints_list
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.sports.sport import Sport


def constraint_checker(sports: list[Sport], events: list[Event], general_constraints: list[str]) -> list:
    conflicts = []

    for sport in sports:
        for constraint_string in sport.constraints:
            if not (constraint_string in constraints_list):
                handle_error("Constraint not valid: " + constraint_string)

            sport_specific_events = [event for event in events if event.sport.name == sport.name]

            constraint = constraints_list[constraint_string]
            conflicts += constraint_check(constraint, sport_specific_events)

    for constraint_string in general_constraints:
        if not (constraint_string in constraints_list):
            handle_error("Constraint not valid: " + constraint_string)

        constraint = constraints_list[constraint_string]
        conflicts += constraint_check(constraint, events)

    return conflicts


def constraint_check(constraint: Constraint, events: list[Event]) -> list:
    if constraint.constraint_type == ConstraintType.UNARY:
        result = unary_constraint_check(constraint, events)
    elif constraint.constraint_type == ConstraintType.BINARY:
        result = binary_constraint_check(constraint, events)
    else:
        result = all_event_constraint_check(constraint, events)
    return result


def valid_constraint_check(constraint: Constraint, events: list[Event]) -> bool:
    return len(constraint_check(constraint, events)) == 0


def unary_constraint_check(constraint: Constraint, events) -> list:
    conflicts = []
    for event in events:
        if not constraint.constraint.function(event):
            conflicts.append([constraint.constraint.string_name, [event.event_id]])

    return conflicts


def binary_constraint_check(constraint: Constraint, events) -> list:
    conflicts = []

    for event_1 in range(len(events)):
        for event_2 in range(event_1 + 1, len(events)):
            if not constraint.constraint.function(events[event_1], events[event_2]):
                conflicts.append([constraint.constraint.string_name,
                                  [events[event_1].sport.name, str(events[event_1].event_id),
                                   str(events[event_2].event_id)]])

    return conflicts


def all_event_constraint_check(constraint: Constraint, events):
    conflicts = []
    if not constraint.constraint.function(events):
        conflicts.append([constraint.constraint.string_name, events])

    return conflicts

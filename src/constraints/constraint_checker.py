from src.constraints.constraint import ConstraintType, constraints_list, get_constraint_from_string, ConstraintFunction
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.sports.sport import Sport


def constraint_checker(sports: list[Sport], events: list[Event], general_constraints: list[str],
                       params: object) -> list:
    conflicts = []

    for sport in sports:
        for constraint_string in sport.constraints:
            sport_specific_events = [event for event in events if event.sport.name == sport.name]

            constraint = get_constraint_from_string(constraint_string)
            conflicts += constraint_check(constraint, sport_specific_events, params)

    for constraint_string in general_constraints:
        if not (constraint_string in constraints_list):
            handle_error("Constraint not valid: " + constraint_string)

        constraint = get_constraint_from_string(constraint_string)
        conflicts += constraint_check(constraint, events, params)

    return conflicts


def constraint_check(constraint: ConstraintFunction, events: list[Event], params: object) -> list:
    if constraint.constraint_type == ConstraintType.UNARY:
        result = unary_constraint_check(constraint, events, params)
    elif constraint.constraint_type == ConstraintType.BINARY:
        result = binary_constraint_check(constraint, events, params)
    else:
        result = all_event_constraint_check(constraint, events, params)
    return result


def valid_constraint_check(constraint: ConstraintFunction, events: list[Event], params: object) -> bool:
    return len(constraint_check(constraint, events, params)) == 0


def unary_constraint_check(constraint: ConstraintFunction, events, params: object) -> list:
    conflicts = []
    for event in events:
        if not constraint.function(params, event):
            conflicts.append([constraint.string_name, [event.event_id]])

    return conflicts


def binary_constraint_check(constraint: ConstraintFunction, events, params: object) -> list:
    conflicts = []

    for event_1 in range(len(events)):
        for event_2 in range(event_1 + 1, len(events)):
            if not constraint.function(params, events[event_1], events[event_2]):
                conflicts.append([constraint.string_name,
                                  [events[event_1].sport.name, str(events[event_1].event_id),
                                   str(events[event_2].event_id)]])

    return conflicts


def all_event_constraint_check(constraint: ConstraintFunction, events, params: object):
    conflicts = []
    if not constraint.function(params, events):
        conflicts.append([constraint.string_name, events])

    return conflicts

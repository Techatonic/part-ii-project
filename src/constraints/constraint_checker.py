from src.constraints.constraint import ConstraintType, constraints_list, get_constraint_from_string, ConstraintFunction
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.sports.sport import Sport
from src.helper.helper import get_alL_events


def constraint_checker(sports: dict[str, Sport], events: dict[str, list[Event]],
                       general_constraints: dict) -> list:
    conflicts = []

    for sport_name in sports:
        # TODO: Only handles required constraints at the moment
        for constraint_string in sports[sport_name].constraints['required']:
            constraint = get_constraint_from_string(constraint_string)
            conflicts += constraint_check(constraint, events[sport_name])
            if sport_name == "boxing_heavyweight":
                print(sport_name, constraint_string, constraint_check(constraint, events[sport_name]))

    for constraint_string in general_constraints['required']:
        if not (constraint_string in constraints_list):
            handle_error("Constraint not valid: " + constraint_string)

        constraint = get_constraint_from_string(constraint_string)

        all_events = get_alL_events(events)
        conflicts += constraint_check(constraint, all_events)

    return conflicts


def constraint_check(constraint: ConstraintFunction, events) -> list:
    if constraint.constraint_type == ConstraintType.UNARY:
        result = unary_constraint_check(constraint, events)
    elif constraint.constraint_type == ConstraintType.BINARY:
        result = binary_constraint_check(constraint, events)
    else:
        result = all_event_constraint_check(constraint, events)
    return result


def valid_constraint_check(constraint: ConstraintFunction, events) -> bool:
    return len(constraint_check(constraint, events)) == 0


def unary_constraint_check(constraint: ConstraintFunction, events) -> list:
    conflicts = []
    for event in events:
        if not constraint.function(events[event]):
            conflicts.append([constraint.string_name, [event]])

    return conflicts


def binary_constraint_check(constraint: ConstraintFunction, events) -> list:
    conflicts = []

    for event_1 in range(len(events)):
        for event_2 in range(event_1 + 1, len(events)):
            if not constraint.function(events[event_1], events[event_2]):
                conflicts.append([constraint.string_name,
                                  [events[event_1].sport.name, str(event_1), str(event_2)]])

    return conflicts


def all_event_constraint_check(constraint: ConstraintFunction, events):
    conflicts = []
    if not constraint.function(events):
        conflicts.append([constraint.string_name, events])

    return conflicts

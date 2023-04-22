from src.constraints.constraint import ConstraintType, constraints_list, get_constraint_from_string, Constraint
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.sports.sport import Sport
from src.helper.helper import get_alL_events, convert_events_list_to_dict

from typing import Type


def constraint_checker(sports: dict[str, Sport], events: dict[str, list[Event]],
                       general_constraints: dict) -> list:
    conflicts = []

    for sport_name in sports:
        # TODO: Only handles required constraints at the moment
        for constraint_string in sports[sport_name].constraints['required']:
            constraint = get_constraint_from_string(constraint_string)(events, sports, None)
            curr_conflicts = constraint_check(constraint, events[sport_name], constraint_checker_flag=True)
            if len(curr_conflicts) > 0:
                conflicts.append(curr_conflicts)

    for constraint_string in general_constraints['required']:
        if not (constraint_string in constraints_list):
            handle_error("Constraint not valid: " + constraint_string)

        constraint = get_constraint_from_string(constraint_string)(events, sports, None)
        all_events = get_alL_events(events)
        curr_conflicts = constraint_check(constraint, all_events, constraint_checker_flag=True)
        if len(curr_conflicts) > 0:
            conflicts.append(curr_conflicts)

    return conflicts


def constraint_check(constraint: Type[Constraint], events, constraint_checker_flag=False) -> list:
    if constraint.constraint_type == ConstraintType.UNARY:
        result = unary_constraint_check(constraint, events, constraint_checker_flag)
    elif constraint.constraint_type == ConstraintType.BINARY:
        result = binary_constraint_check(constraint, events, constraint_checker_flag)
    else:
        result = all_event_constraint_check(constraint, events, constraint_checker_flag)
    return result


def valid_constraint_check(constraint: Type[Constraint], events) -> bool:
    return len(constraint_check(constraint, events)) == 0


# TODO: If I keep changes to constraint class, fix this
def single_constraint_check(constraint: Type[Constraint], *events) -> bool:
    events = convert_events_list_to_dict(list(events))
    return len(constraint.solve(constraint, events)) == 0


def unary_constraint_check(constraint: Type[Constraint], events, constraint_checker_flag) -> list:
    conflicts = []
    for event in events:
        result = constraint.solve({event: events[event]}, constraint_check=constraint_checker_flag)
        if len(result) > 0:
            conflicts += result
    return [constraint.constraint_string, conflicts] if len(conflicts) > 0 else []


def binary_constraint_check(constraint: Type[Constraint], events, constraint_checker_flag) -> list:
    conflicts = []

    for event_1 in range(len(events)):
        for event_2 in range(event_1 + 1, len(events)):
            result = constraint.solve({event_1: events[event_1], event_2: events[event_2]},
                                      constraint_check=constraint_checker_flag)
            if len(result) > 0:
                conflicts += result

    return [constraint.constraint_string, conflicts] if len(conflicts) > 0 else []


def all_event_constraint_check(constraint: Type[Constraint], events, constraint_checker_flag):
    conflicts = constraint.solve(constraint, events, constraint_check=constraint_checker_flag)
    return [constraint.constraint_string, conflicts] if len(conflicts) > 0 else []

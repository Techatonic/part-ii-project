from src.constraints.constraint import constraints_list, ConstraintType
from src.error_handling.handle_error import handle_error
from src.constraints.constraint import same_venue_overlapping_time


def constraint_checker(tournament_length, sports, events, general_constraints):
    conflicts = []

    for sport in sports:
        for constraint_string in sport.constraints:
            if not (constraint_string in constraints_list):
                handle_error("Constraint not valid: " + constraint_string)
                return

            sport_specific_events = [event for event in events if event.sport.name == sport.name]

            constraint = constraints_list[constraint_string]
            # print(constraint)

            if constraint.constraint_type == ConstraintType.UNARY:
                result = unary_constraint_check(constraint, sport_specific_events)
            elif constraint.constraint_type == ConstraintType.BINARY:
                result = binary_constraint_check(constraint, sport_specific_events)
            else:
                result = all_event_constraint_check(constraint, sport_specific_events)

            conflicts += result

    for constraint_string in general_constraints:
        if not (constraint_string in constraints_list):
            handle_error("Constraint not valid: " + constraint_string)
            return

        constraint = constraints_list[constraint_string]
        if constraint.constraint_type == ConstraintType.UNARY:
            result = unary_constraint_check(constraint, events)
        elif constraint.constraint_type == ConstraintType.BINARY:
            result = binary_constraint_check(constraint, events)
        else:
            result = all_event_constraint_check(constraint, events)
        conflicts += result

    return conflicts


def unary_constraint_check(constraint, events):
    conflicts = []
    for event in events:
        if not constraint.function(event):
            conflicts.append([constraint.string_name, [event.event_num]])

    return conflicts


def binary_constraint_check(constraint, events):
    conflicts = []
    for event_1 in range(len(events)):
        for event_2 in range(event_1 + 1, len(events)):
            if not constraint.function(events[event_1], events[event_2]):
                conflicts.append([constraint.string_name,
                                  [events[event_1].sport.name + "_" + str(events[event_1].event_num),
                                   events[event_2].sport.name + "_" + str(events[event_2].event_num)]])

    return conflicts


def all_event_constraint_check(constraint, events):
    conflicts = []
    print(events)
    if not constraint.function(events):
        conflicts.append([constraint.string_name, events])

    return conflicts

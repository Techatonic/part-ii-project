from enum import Enum

from src.error_handling.handle_error import handle_error


def same_venue_overlapping_time(a, b):
    if not (a.venue == b.venue and a.day == b.day and (
            (a.start_time <= b.start_time < a.start_time + a.duration) or
            (b.start_time <= a.start_time < b.start_time + b.duration)
    )):
        return True
    return False


def no_later_rounds_before_earlier_rounds(a, b):
    return a.sport == b.sport and \
           (a.round.round_index == b.round.round_index or
            a.round.round_index > b.round.round_index and a.day < b.day or
            a.round.round_index < b.round.round_index and b.day < a.day)


def same_venue_max_matches_per_day(*variables):
    venues = {}
    if type(variables) == tuple:
        if len(variables) == 1:
            variables = variables[0]
    # pprint.pprint(variables)
    for event in variables:
        # print(event)
        if not (event.venue.name in venues):
            venues[event.venue.name] = {event.day: 1}
        else:
            if not (event.day in venues[event.venue.name]):
                venues[event.venue.name][event.day] = 1
            else:
                venues[event.venue.name][event.day] += 1
            if venues[event.venue.name][event.day] > event.venue.max_matches_per_day:
                # print(venues)
                return False
    # print("Works: ", venues)
    return True


class ConstraintType(Enum):
    UNARY = 1,
    BINARY = 2,
    ALL = 3


class Constraint:
    def __init__(self, string_name, function, constraint_type: ConstraintType):
        self.string_name = string_name
        self.function = function
        self.constraint_type = constraint_type

    def __eq__(self, other):
        return self.string_name == other.string_name and self.sport_constraint == other.sport_constraint


# Dictionary of constraints
constraints_list = {
    "same_venue_overlapping_time": Constraint("same_venue_overlapping_time", same_venue_overlapping_time,
                                              ConstraintType.BINARY),
    "no_later_rounds_before_earlier_rounds": Constraint("same_venue_overlapping_time",
                                                        no_later_rounds_before_earlier_rounds, ConstraintType.BINARY),
    "same_venue_max_matches_per_day": Constraint("same_venue_overlapping_time", same_venue_max_matches_per_day,
                                                 ConstraintType.ALL)
}


def get_constraint(string):
    if not (string in constraints_list):
        handle_error("Constraint does not exist: " + string)
    return constraints_list[string]

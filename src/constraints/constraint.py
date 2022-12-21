from enum import Enum

from src.error_handling.handle_error import handle_error
from src.sports.sport import Sport


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
    for event in variables:
        venue_name = event.venue.name
        if not (venue_name in venues):
            venues[venue_name] = {event.day: 1}
        else:
            if not (event.day in venues[venue_name]):
                venues[venue_name][event.day] = 1
            else:
                venues[venue_name][event.day] += 1
            if venues[venue_name][event.day] > event.venue.max_matches_per_day:
                return False
    return True

def same_sport_max_matches_per_day(*variables):
    sports = {}
    if type(variables) == tuple:
        if len(variables) == 1:
            variables = variables[0]
    for event in variables:
        sport_name = event.sport.name
        if not (sport_name in sports):
            sports[sport_name] = {event.day: 1}
        else:
            if not (event.day in sports[sport_name]):
                sports[sport_name][event.day] = 1
            else:
                sports[sport_name][event.day] += 1
            if sports[sport_name][event.day] > event.sport.max_matches_per_day:
                return False
    return True

def time_between_matches(*variables):
    return True


class ConstraintType(Enum):
    UNARY = 1,
    BINARY = 2,
    ALL = 3


class ConstraintFunction:
    def __init__(self, string_name, function, constraint_type: ConstraintType):
        self.string_name = string_name
        self.function = function
        self.constraint_type = constraint_type

    def __eq__(self, other):
        # TODO Fix this
        return self.string_name == other.string_name


class Constraint:
    def __init__(self, constraint: ConstraintFunction, variables=None, sport: Sport = None):
        self.constraint = constraint
        self.variables = variables
        self.sport = sport

        if self.variables is None:
            self.constraint_type = ConstraintType.ALL
        elif len(self.variables) == 1:
            self.constraint_type = ConstraintType.UNARY
        elif len(self.variables) == 2:
            self.constraint_type = ConstraintType.BINARY
        else:
            handle_error(
                "Invalid number of variables for constraint. At the moment, only unary,"
                " binary and all constraints are permitted")

    def __str__(self):
        return f"""{{
            constraint: {self.constraint.string_name},
            variables: {self.variables},
            sport: {self.sport},
            constraint_type: {self.constraint_type}
        \n}}"""


# Dictionary of constraints
constraints_list = {
    "same_venue_overlapping_time": ConstraintFunction("same_venue_overlapping_time", same_venue_overlapping_time,
                                                      ConstraintType.BINARY),
    "no_later_rounds_before_earlier_rounds": ConstraintFunction("no_later_rounds_before_earlier_rounds",
                                                                no_later_rounds_before_earlier_rounds,
                                                                ConstraintType.BINARY),
    "same_venue_max_matches_per_day": ConstraintFunction("same_venue_max_matches_per_day",
                                                         same_venue_max_matches_per_day,
                                                         ConstraintType.ALL),
    "time_between_matches": ConstraintFunction("time_between_matches", time_between_matches, ConstraintType.ALL),
    "max_matches_per_day": ConstraintFunction("max_matches_per_day", same_sport_max_matches_per_day, ConstraintType.ALL)
}


def get_constraint_from_string(string):
    if not (string in constraints_list):
        handle_error("Constraint does not exist: " + string)
    return constraints_list[string]


def get_constraint_string_from_lambda(function):
    for key in constraints_list:
        if constraints_list[key].function == function:
            return key

    handle_error("Constraint does not exist")

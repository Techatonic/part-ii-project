from enum import Enum

from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import reformat_assignments
from src.solvers.solver import Solver
from src.sports.sport import Sport


# Constraint Definitions
def same_venue_overlapping_time_constraint_check(csp_instance: Solver, params, a, b) -> bool:
    if not (a.venue == b.venue and a.day == b.day and (
            (a.start_time <= b.start_time < a.start_time + a.duration) or
            (b.start_time <= a.start_time < b.start_time + b.duration)
    )):
        return True
    return False


def same_venue_overlapping_time(csp_instance: Solver, params: dict, *variables: list[Event]) -> bool:
    variables = reformat_assignments(variables)

    venues = {}
    for event in variables:
        venue_name = event.venue.name
        if not venue_name in venues:
            venues[venue_name] = {
                event.day: [[event.start_time, event.start_time + event.duration]]
            }
        else:
            if not event.day in venues[venue_name]:
                venues[venue_name][event.day] = [[event.start_time, event.start_time + event.duration]]
            else:
                for time_check in venues[venue_name][event.day]:
                    if (event.start_time <= time_check[0] < event.start_time + event.duration) or \
                            (time_check[0] <= event.start_time < time_check[0] + time_check[1]):
                        return False
                venues[venue_name][event.day].append([event.start_time, event.start_time + event.duration])
    return True


def team_time_between_matches(csp_instance: Solver, params: dict, *variables: list[Event]) -> bool:
    variables = reformat_assignments(variables)
    if len(variables) == 0:
        return True
    teams = {}
    sport = variables[0].sport.name
    for event in variables:
        event_day = event.day
        if event.teams_involved is None:
            continue
        for team in event.teams_involved:
            if not (team in teams):
                teams[team] = [event_day]
            else:
                for other_day in teams[team]:
                    if abs(event_day - other_day) < params["min_time_between_matches"]:
                        return False
                teams[team].append(event_day)
    return True


def venue_time_between_matches(csp_instance: Solver, params: dict, *variables: list[Event]) -> bool:
    variables = reformat_assignments(variables)
    if len(variables) == 0:
        return True
    venues = {}
    sport = variables[0].sport.name
    for event in variables:
        venue_name = event.venue.name
        if not (venue_name in venues):
            venues[venue_name] = {event.day: [event.start_time]}
        else:
            if not (event.day in venues[venue_name]):
                venues[venue_name][event.day] = [event.start_time]
            else:
                for other_time in venues[venue_name][event.day]:
                    if abs(event.start_time + event.duration - other_time) < \
                            params["min_time_between_matches"] or \
                            abs(event.start_time - (other_time + event.duration)) < \
                            params["min_time_between_matches"]:
                        return False
                venues[venue_name][event.day].append(event.start_time)
    return True


def no_later_rounds_before_earlier_rounds_constraint_check(csp_instance: Solver, params: dict, a, b) -> bool:
    return a.sport == b.sport and \
        (a.round.round_index == b.round.round_index or
         a.round.round_index > b.round.round_index and a.day <= b.day or
         a.round.round_index < b.round.round_index and b.day <= a.day)


def no_later_rounds_before_earlier_rounds(csp_instance: Solver, params: dict, *variables: list[Event]) -> bool:
    variables = reformat_assignments(variables)

    sports = {}
    for variable in variables:
        if not (variable.sport.name in sports):
            sports[variable.sport.name] = {variable.round.round_index: [variable]}
        else:
            if not (variable.round.round_index in sports[variable.sport.name]):
                sports[variable.sport.name][variable.round.round_index] = [variable]
            else:
                sports[variable.sport.name][variable.round.round_index].append(variable)
    variables_by_sport = sports.values()

    for sport_variables in variables_by_sport:
        for _round in set(sport_variables.keys()):
            vals = sport_variables[_round]
            sport_variables[_round] = [min(vals, key=lambda event: event.day).day,
                                       max(vals, key=lambda event: event.day).day]
        sorted_rounds = list(reversed(sorted(set(sport_variables.keys()))))

        for index in range(len(sorted_rounds) - 1):
            if sport_variables[sorted_rounds[index]][1] >= sport_variables[sorted_rounds[index + 1]][0]:
                return False
    return True


def same_venue_max_matches_per_day(csp_instance: Solver, params: dict, *variables: list[Event]) -> bool:
    variables = reformat_assignments(variables)
    venues = {}

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


def same_sport_max_matches_per_day(csp_instance: Solver, params: dict, *variables: list[Event]) -> bool:
    sports = {}
    variables = reformat_assignments(variables)
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


def max_capacity_at_final(csp_instance: Solver, params: dict, event: Event):
    return not (event.round.round_index == 0) or event.venue == max(csp_instance.data["venues"],
                                                                    key=lambda venue: venue.capacity)


# Constraint class definitions

class ConstraintType(Enum):
    UNARY = 1,
    BINARY = 2,
    ALL = 3


class ConstraintFunction:
    def __init__(self, string_name, function, constraint_type: ConstraintType):
        self.string_name = string_name
        self.function = function
        self.constraint_type = constraint_type

    def __eq__(self, other) -> bool:
        # TODO Fix this
        return self.string_name == other.string_name


class Constraint:
    def __init__(self, constraint: ConstraintFunction, variables=None, sport: Sport = None, params: dict = None):
        self.constraint = constraint
        self.variables = variables
        self.sport = sport
        self.params = params

        self.constraint_type = self.constraint.constraint_type

    def __str__(self) -> str:
        return f"""{{
            constraint: {self.constraint.string_name},
            variables: {self.variables},
            sport: {self.sport},
            constraint_type: {self.constraint_type}
        \n}}"""

    def __eq__(self, other):
        return self.constraint.string_name == other.constraint.string_name and self.sport == other.sport and \
            self.params == other.params

    def __hash__(self):
        hash((self.constraint.string_name, self.sport, self.constraint_type, self.params))


# Helper Functions
def get_constraint_from_string(string: str) -> ConstraintFunction:
    if not (string in constraints_list):
        handle_error("Constraint does not exist: " + string)
    return constraints_list[string]


def get_constraint_string_from_lambda(function) -> str:
    for key in constraints_list:
        if constraints_list[key].function == function:
            return key

    handle_error("Constraint does not exist")


# Params and constraint list
constraints_list = {
    "same_venue_overlapping_time_constraint_check": ConstraintFunction(
        "same_venue_overlapping_time_constraint_check",
        same_venue_overlapping_time_constraint_check,
        ConstraintType.BINARY),
    "same_venue_overlapping_time": ConstraintFunction("same_venue_overlapping_time", same_venue_overlapping_time,
                                                      ConstraintType.ALL),
    "no_later_rounds_before_earlier_rounds_constraint_check": ConstraintFunction(
        "no_later_rounds_before_earlier_rounds_constraint_check",
        no_later_rounds_before_earlier_rounds_constraint_check,
        ConstraintType.BINARY),
    "no_later_rounds_before_earlier_rounds": ConstraintFunction("no_later_rounds_before_earlier_rounds",
                                                                no_later_rounds_before_earlier_rounds,
                                                                ConstraintType.ALL),
    "same_venue_max_matches_per_day": ConstraintFunction("same_venue_max_matches_per_day",
                                                         same_venue_max_matches_per_day,
                                                         ConstraintType.ALL),
    "team_time_between_matches": ConstraintFunction("team_time_between_matches", team_time_between_matches,
                                                    ConstraintType.ALL),
    "venue_time_between_matches": ConstraintFunction("venue_time_between_matches", venue_time_between_matches,
                                                     ConstraintType.ALL),
    "max_matches_per_day": ConstraintFunction("max_matches_per_day", same_sport_max_matches_per_day,
                                              ConstraintType.ALL),
    "max_capacity_at_final": ConstraintFunction("max_capacity_at_final", max_capacity_at_final, ConstraintType.UNARY)
}

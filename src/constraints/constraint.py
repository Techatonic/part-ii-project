from enum import Enum

from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper import global_variables
from src.helper.helper import remove_tuple_from_events, remove_duplicates_from_list
from src.sports.sport import Sport


# Constraint Definitions
# TODO Check if constraint check version is really needed here. Or even if it's used. If it is used, it should be removed
#  because it can be replaced with the 'ALL' version
def same_venue_overlapping_time_constraint_check(a, b, constraint_check=False) -> list[str]:
    if not (a.venue == b.venue and a.day == b.day and (
            (a.start_time <= b.start_time < a.start_time + a.duration) or
            (b.start_time <= a.start_time < b.start_time + b.duration)
    )):
        return []
    return [a, b]


def same_venue_overlapping_time(*variables: dict[str, Event], constraint_check=False) -> list[str]:
    variables = remove_tuple_from_events(variables)
    variables = list(variables.values()) if type(variables) == dict else variables
    venues = {}
    conflicts = []
    for event in variables:
        venue_name = event.venue.name
        if not venue_name in venues:
            venues[venue_name] = {
                event.day: {event.event_id: [event.start_time, event.start_time + event.duration]}
            }
        else:
            if not event.day in venues[venue_name]:
                venues[venue_name][event.day] = {event.event_id: [event.start_time, event.start_time + event.duration]}
            else:
                for other_event, time_check in venues[venue_name][event.day].items():
                    if (event.start_time <= time_check[0] < event.start_time + event.duration) or \
                            (time_check[0] <= event.start_time < time_check[0] + time_check[1]):
                        if not constraint_check:
                            return [event.event_id, other_event]
                        conflicts += [event.event_id, other_event]
                venues[venue_name][event.day][event.event_id] = [event.start_time, event.start_time + event.duration]
    return remove_duplicates_from_list(conflicts)


def team_time_between_matches(*variables: dict[str, Event], constraint_check=False) -> list[str]:
    variables = remove_tuple_from_events(variables)
    variables = list(variables.values()) if type(variables) == dict else variables
    conflicts = []
    if len(variables) == 0:
        return [] if constraint_check else True
    teams = {}
    sport = variables[0].sport.name
    for event in variables:
        event_day = event.day
        if event.teams_involved is None:
            continue
        for team in event.teams_involved:
            if not (team in teams):
                teams[team] = {event.event_id: event_day}
            else:
                for other_event, other_day in teams[team].items():
                    if abs(event_day - other_day) < \
                            global_variables.constraint_params[sport]["required"]["team_time_between_matches"][
                                "min_time_between_matches"]:
                        if not constraint_check:
                            return [event.event_id, other_event]
                        conflicts += [event.event_id, other_event.event_id]
                teams[team][event.event_id] = event_day
    return remove_duplicates_from_list(conflicts)


def venue_time_between_matches(*variables: dict[str, Event], constraint_check=False) -> list[str]:
    variables = remove_tuple_from_events(variables)
    variables = list(variables.values()) if type(variables) == dict else variables
    conflicts = []
    if len(variables) == 0:
        return [] if constraint_check else True
    venues = {}
    sport = variables[0].sport.name
    for event in variables:
        venue_name = event.venue.name
        if not (venue_name in venues):
            venues[venue_name] = {event.day: {event.event_id: event.start_time}}
        else:
            if not (event.day in venues[venue_name]):
                venues[venue_name][event.day] = {event.event_id: event.start_time}
            else:
                for other_event, other_time in venues[venue_name][event.day].items():
                    if abs(event.start_time + event.duration - other_time) < \
                            global_variables.constraint_params[sport]["required"]["venue_time_between_matches"][
                                "min_time_between_matches"] or \
                            abs(event.start_time - (other_time + event.duration)) < \
                            global_variables.constraint_params[sport]["required"]["venue_time_between_matches"][
                                "min_time_between_matches"]:
                        if not constraint_check:
                            return [event.event_id, other_event]
                        conflicts += [event.event_id, other_event]
                venues[venue_name][event.day][event.event_id] = event.start_time

    return remove_duplicates_from_list(conflicts)


# TODO See above TODO comment - is constraint check version needed?
def no_later_rounds_before_earlier_rounds_constraint_check(a: Event, b: Event, constraint_check=False) -> list[str]:
    bool_val = a.sport == b.sport and \
               (a.round.round_index == b.round.round_index or
                a.round.round_index > b.round.round_index and a.day <= b.day or
                a.round.round_index < b.round.round_index and b.day <= a.day)
    return [] if bool_val else [a.event_id, b.event_id]


def no_later_rounds_before_earlier_rounds(*variables: dict[str, Event], constraint_check=False) -> list[str]:
    variables = remove_tuple_from_events(variables)
    variables = list(variables.values()) if type(variables) == dict else variables
    sports = {}
    conflicts = []
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
        min_max_days = {}
        for _round in set(sport_variables.keys()):
            vals = sport_variables[_round]
            min_max_days[_round] = [min(vals, key=lambda event: event.day).day,
                                    max(vals, key=lambda event: event.day).day]
        sorted_rounds = list(reversed(sorted(set(min_max_days.keys()))))

        for index in range(len(sorted_rounds) - 1):
            if min_max_days[sorted_rounds[index]][1] >= min_max_days[sorted_rounds[index + 1]][0]:
                # Get all conflicting events
                for event_1 in sport_variables[sorted_rounds[index]]:
                    for event_2 in sport_variables[sorted_rounds[index + 1]]:
                        if event_1.day >= event_2.day:
                            if not constraint_check:  # If we're not getting all conflicting events, we just return one
                                return [event_1.event_id]
                            conflicts += [event_1.event_id, event_2.event_id]

    return remove_duplicates_from_list(conflicts)


def same_venue_max_matches_per_day(*variables: dict[str, Event], constraint_check=False) -> list[str]:
    variables = remove_tuple_from_events(variables)
    variables = list(variables.values()) if type(variables) == dict else variables
    venues = {}
    conflicts = []

    for event in variables:
        venue_name = event.venue.name
        if not (venue_name in venues):
            venues[venue_name] = {event.day: [event.event_id]}
        else:
            if not (event.day in venues[venue_name]):
                venues[venue_name][event.day] = [event.event_id]
            else:
                venues[venue_name][event.day].append(event.event_id)
            if len(venues[venue_name][event.day]) > event.venue.max_matches_per_day:
                if not constraint_check:
                    return venues[venue_name][event.day]
                conflicts += venues[venue_name][event.day]
    return remove_duplicates_from_list(conflicts)


def same_sport_max_matches_per_day(*variables: dict[str, Event], constraint_check=False) -> list[str]:
    sports = {}
    variables = remove_tuple_from_events(variables)
    variables = list(variables.values()) if type(variables) == dict else variables
    conflicts = []
    for event in variables:
        sport_name = event.sport.name
        if not (sport_name in sports):
            sports[sport_name] = {event.day: [event.event_id]}
        else:
            if not (event.day in sports[sport_name]):
                sports[sport_name][event.day] = [event.event_id]
            else:
                sports[sport_name][event.day].append(event.event_id)
            if len(sports[sport_name][event.day]) > event.sport.max_matches_per_day:
                if not constraint_check:
                    return sports[sport_name][event.day]
                conflicts += sports[sport_name][event.day]
    return remove_duplicates_from_list(conflicts)


def max_capacity_at_final(event: Event, constraint_check=False) -> list[str]:
    sport = event.sport
    bool_val = not (event.round.round_index == 0) or event.venue == max(global_variables.venues[sport.name],
                                                                        key=lambda venue: venue.capacity)
    return [] if bool_val else [event.event_id]


def valid_match_time(event: Event, constraint_check=False) -> list[str]:
    sport = event.sport
    bool_val = sport.min_start_day <= event.day <= sport.max_finish_day and \
               sport.min_start_time <= event.start_time and \
               event.start_time + event.duration <= sport.max_finish_time
    # if event.event_id == "football_31":
    #    print("football_31: ", bool_val)
    return [] if bool_val else [event.event_id]


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
        self.relevant_features = []

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
    "max_capacity_at_final": ConstraintFunction("max_capacity_at_final", max_capacity_at_final, ConstraintType.UNARY),
    "valid_match_time": ConstraintFunction("valid_match_time", valid_match_time, ConstraintType.UNARY)
}

from abc import ABC, abstractmethod
from enum import Enum

from src.helper.handle_error import handle_error
from src.events.event import Event
from src.helper import global_variables
from src.helper.helper import remove_tuple_from_events, remove_duplicates_from_list
from src.sports.sport import Sport


class ConstraintType(Enum):
    UNARY = 1,
    BINARY = 2,
    ALL = 3


class Constraint(ABC):
    _constraint_string = "NotImplementedError"
    _variables = "NotImplementedError"
    _sport = "NotImplementedError"
    _constraint_type = "NotImplementedError"
    _params = "NotImplementedError"

    def get_constraint_string(self):
        if self._constraint_string == "NotImplementedError":
            handle_error("Constraint has not been constructed")
        return self._constraint_string

    def get_variables(self):
        if self._variables == "NotImplementedError":
            handle_error("Constraint has not been constructed")
        return self._variables

    def get_sport(self):
        if self._sport == "NotImplementedError":
            handle_error("Constraint has not been constructed")
        return self._sport

    def get_constraint_type(self):
        if self._constraint_type == "NotImplementedError":
            handle_error("Constraint has not been constructed")
        return self._constraint_type

    def get_params(self):
        if self._params == "NotImplementedError":
            handle_error("Constraint has not been constructed")
        return self._params

    @abstractmethod
    def eval_constraint(self, variables, constraint_check=False):
        pass

    def __str__(self) -> str:
        return f"""{{
            constraint: {self._constraint_string},
            variables: {self._variables},
            sport: {self._sport},
            constraint_type: {self._constraint_type}
        \n}}"""

    def __eq__(self, other):
        return self._constraint_string == other.get_constraint_string() and self._variables == other.get_variables()

    def __hash__(self):
        hash((self._constraint_string, self._sport, self._constraint_type, self._params, self._variables))


class SameVenueOverlappingTime(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "same_venue_overlapping_time"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, *variables: dict[str, Event], constraint_check=False) -> list[str]:
        if isinstance(variables[0], type(self)):
            variables = variables[1:]
        variables = remove_tuple_from_events(variables)
        variables = list(variables.values()) if type(variables) == dict else variables
        venues = {}
        conflicts = []
        for event in variables:
            venue_name = event.venue.name
            if not venue_name in venues:
                venues[venue_name] = {
                    event.day: {event.id: [event.start_time, event.start_time + event.duration]}
                }
            else:
                if not event.day in venues[venue_name]:
                    venues[venue_name][event.day] = {
                        event.id: [event.start_time, event.start_time + event.duration]}
                else:
                    for other_event, time_check in venues[venue_name][event.day].items():
                        if (event.start_time <= time_check[0] < event.start_time + event.duration) or \
                                (time_check[0] <= event.start_time < time_check[0] + time_check[1]):
                            if not constraint_check:
                                # print(3, [event.event_id, other_event])
                                return [event.id, other_event]
                            conflicts += [event.id, other_event]
                    venues[venue_name][event.day][event.id] = [event.start_time,
                                                               event.start_time + event.duration]
        # print(3, remove_duplicates_from_list(conflicts))
        return remove_duplicates_from_list(conflicts)


class TeamTimeBetweenMatches(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "team_time_between_matches"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, *variables: dict[str, Event], constraint_check=False) -> list[str]:
        if isinstance(variables[0], type(self)):
            variables = variables[1:]
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
                    teams[team] = {event.id: event_day}
                else:
                    for other_event, other_day in teams[team].items():
                        if abs(event_day - other_day) < \
                                global_variables.constraint_params[sport]["required"]["team_time_between_matches"][
                                    "min_time_between_matches"]:
                            if not constraint_check:
                                # print(4, [event.event_id, other_event])
                                return [event.id, other_event]
                            conflicts += [event.id, other_event]
                    teams[team][event.id] = event_day
        # print(4, remove_duplicates_from_list(conflicts))
        return remove_duplicates_from_list(conflicts)


class VenueTimeBetweenMatches(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "venue_time_between_matches"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, *variables: dict[str, Event], constraint_check=False) -> list[str]:
        if isinstance(variables[0], type(self)):
            variables = variables[1:]
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
                venues[venue_name] = {event.day: {event.id: event.start_time}}
            else:
                if not (event.day in venues[venue_name]):
                    venues[venue_name][event.day] = {event.id: event.start_time}
                else:
                    for other_event, other_time in venues[venue_name][event.day].items():
                        if abs(event.start_time + event.duration - other_time) < \
                                global_variables.constraint_params[sport]["required"]["venue_time_between_matches"][
                                    "min_time_between_matches"] or \
                                abs(event.start_time - (other_time + event.duration)) < \
                                global_variables.constraint_params[sport]["required"]["venue_time_between_matches"][
                                    "min_time_between_matches"]:
                            if not constraint_check:
                                # print("err", [event.event_id, other_event])
                                return [event.id, other_event]
                            conflicts += [event.id, other_event]
                    venues[venue_name][event.day][event.id] = event.start_time
        # print(5, remove_duplicates_from_list(conflicts))
        return remove_duplicates_from_list(conflicts)


class NoLaterRoundsBeforeEarlierRounds(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "no_later_rounds_before_earlier_rounds"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, *variables: dict[str, Event], constraint_check=False) -> list[str]:
        if isinstance(variables[0], type(self)):
            variables = variables[1:]
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
                                    # print("err", [event_1.event_id, event_2.event_id])
                                    return [event_1.id, event_2.id]
                                conflicts += [event_1.id, event_2.id]

        # print(7, remove_duplicates_from_list(conflicts))
        return remove_duplicates_from_list(conflicts)


class SameVenueMaxMatchesPerDay(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "same_venue_max_matches_per_day"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, *variables: dict[str, Event], constraint_check=False) -> list[str]:
        if isinstance(variables[0], type(self)):
            variables = variables[1:]
        variables = remove_tuple_from_events(variables)
        variables = list(variables.values()) if type(variables) == dict else variables
        venues = {}
        conflicts = []

        for event in variables:
            venue_name = event.venue.name
            if not (venue_name in venues):
                venues[venue_name] = {event.day: [event.id]}
            else:
                if not (event.day in venues[venue_name]):
                    venues[venue_name][event.day] = [event.id]
                else:
                    venues[venue_name][event.day].append(event.id)
                if len(venues[venue_name][event.day]) > event.venue.max_matches_per_day:
                    if not constraint_check:
                        # print(8, venues[venue_name][event.day])
                        return venues[venue_name][event.day]
                    conflicts += venues[venue_name][event.day]
        # print(8, remove_duplicates_from_list(conflicts))
        return remove_duplicates_from_list(conflicts)


class SameSportMaxMatchesPerDay(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "same_sport_max_matches_per_day"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, *variables: dict[str, Event], constraint_check=False) -> list[str]:
        if isinstance(variables[0], type(self)):
            variables = variables[1:]
        sports = {}
        variables = remove_tuple_from_events(variables)
        variables = list(variables.values()) if type(variables) == dict else variables
        conflicts = []
        for event in variables:
            sport_name = event.sport.name
            if not (sport_name in sports):
                sports[sport_name] = {event.day: [event.id]}
            else:
                if not (event.day in sports[sport_name]):
                    sports[sport_name][event.day] = [event.id]
                else:
                    sports[sport_name][event.day].append(event.id)
                if len(sports[sport_name][event.day]) > int(self.get_params()["max_matches_per_day"]):
                    if not constraint_check:
                        # print(9, sports[sport_name][event.day])
                        return sports[sport_name][event.day]
                    conflicts += sports[sport_name][event.day]
        # print(9, remove_duplicates_from_list(conflicts))
        return remove_duplicates_from_list(conflicts)


class MaxCapacityAtFinal(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "max_capacity_at_final"
        self._constraint_type = ConstraintType.UNARY
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, event: dict[str, Event], constraint_check=False) -> list[str]:
        event = list(event.values())[0]
        bool_val = not (event.round.round_index == 0) or event.venue == max(global_variables.venues[event.sport.name],
                                                                            key=lambda venue: venue.capacity)
        # print(10, [] if bool_val else [event.event_id])
        return [] if bool_val else [event.id]


class ValidMatchTime(Constraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "valid_match_time"
        self._constraint_type = ConstraintType.UNARY
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, event: dict[str, Event], constraint_check=False) -> list[str]:
        event = list(event.values())[0]
        sport = event.sport
        bool_val = sport.min_start_day <= event.day <= sport.max_finish_day and \
                   sport.min_start_time <= event.start_time and \
                   event.start_time + event.duration <= sport.max_finish_time
        # print(11, [] if bool_val else [event.event_id])
        return [] if bool_val else [event.id]


# Helper Functions
def get_constraint_from_string(string: str):  # -> Type[Constraint]:
    if not (string in constraints_list):
        handle_error("Constraint does not exist: " + string)
    return constraints_list[string]


# def get_constraint_string_from_lambda(function) -> str:
#     for key in constraints_list:
#         if constraints_list[key].function == function:
#             return key
#
#     handle_error("Constraint does not exist")


# Params and constraint list
constraints_list = {
    "same_venue_overlapping_time": SameVenueOverlappingTime,
    "no_later_rounds_before_earlier_rounds": NoLaterRoundsBeforeEarlierRounds,
    "same_venue_max_matches_per_day": SameVenueMaxMatchesPerDay,
    "team_time_between_matches": TeamTimeBetweenMatches,
    "venue_time_between_matches": VenueTimeBetweenMatches,
    "max_matches_per_day": SameSportMaxMatchesPerDay,
    "max_capacity_at_final": MaxCapacityAtFinal,
    "valid_match_time": ValidMatchTime,
}

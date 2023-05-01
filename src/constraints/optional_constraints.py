import math
from abc import ABC, abstractmethod
from bisect import insort
import operator
from enum import Enum
from typing import Type

import pgeocode

from src.constraints.constraint import ConstraintType
from src.helper.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import flatten_events_by_sport_to_list
from src.schedulers.solver import Solver
from src.sports.sport import Sport


class OptionalConstraint(ABC):
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
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        pass

    @abstractmethod
    def eval_constraint(self, csp_instance, variables):
        pass

    def __str__(self) -> str:
        return f"""{{
            constraint: {self._constraint_string},
            variables: {self._variables},
            sport: {self._sport},
            constraint_type: {self._constraint_type}
        \n}}"""

    def __eq__(self, other):
        return self._constraint_string == other.constraint.get_constraint_string() and self._variables == other.get_variables()

    def __hash__(self):
        hash((self._constraint_string, self._sport, self._constraint_type, self._params, self._variables))


def take_average_of_heuristics_across_all_sports(csp_instance: Solver,
                                                 assignments_by_sport: dict[str, dict[str, Event]],
                                                 heuristic: Type[OptionalConstraint]) -> float:
    heuristic_count = 0
    sport_count = 0
    for sport in assignments_by_sport:
        _, score = heuristic.eval_constraint(csp_instance, {sport: assignments_by_sport[sport]})
        heuristic_count += score
        sport_count += 1
    return heuristic_count / sport_count


# Optional Constraint Definitions
class MaxMatchesPerDayHeuristic(OptionalConstraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "max_matches_per_day_heuristic"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, csp_instance: Solver, assignments: dict[str, dict[str, Event]]) -> tuple[float, float]:
        # assignments_heuristic = remove_scores_from_dict(assignments)
        events = flatten_events_by_sport_to_list(assignments)

        num_events_to_add = csp_instance.data["num_total_events"] - len(events)

        def get_matches_per_day(temp_assignments: list[Event]):
            # print(temp_assignments)
            temp_assignments_by_day = {}
            for event in temp_assignments:
                if not (event.day in temp_assignments_by_day):
                    temp_assignments_by_day[event.day] = 1
                else:
                    temp_assignments_by_day[event.day] += 1
            return temp_assignments_by_day

        curr = max(get_matches_per_day(events).values())

        def get_new_assignment_day(events):
            days = [event.day for event in events]
            return min(days, key=lambda x: days.count(x))

        for index in range(num_events_to_add):
            new_assignment = events[0].__copy__()
            new_assignment.day = get_new_assignment_day(events)
            events.append(new_assignment)

        assignments_by_day = get_matches_per_day(events)

        optimal = math.ceil(
            csp_instance.data["num_total_events"] / csp_instance.data["tournament_length"])
        score = optimal / max(assignments_by_day.values())

        return curr, score


# class MaximiseSportSpecificConstraints(OptionalConstraint):
#     def set_variables(self, val):
#         self._variables = val
#
#     def __init__(self, variables=None, sport: Sport = None, params: dict = None):
#         self._constraint_string = "maximise_sport_specific_constraints"
#         self._constraint_type = ConstraintType.ALL
#         self._variables = variables
#         self._sport = sport
#         self._params = params
#
#     def eval_constraint(self, csp_instance: Type[Solver], assignments: dict[str, Event]) -> tuple[float, float]:
#         curr = sum(assignments[sport][0] for sport in assignments)
#
#         optimal = 0
#         try:
#             for sport in csp_instance.queue.variables:
#                 optimal += max(option[0] for option in sport.domain)
#         except:
#             handle_error("Non-CSOPSolver solver used when CSOPSolver was expected")
#
#         score = (curr + sum(max(option[0] for option in sport.domain) for sport in csp_instance.queue.variables if
#                             not (sport.variable in assignments))) / optimal
#         return curr, score


class AvgCapacityHeuristic(OptionalConstraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "avg_capacity_heuristic"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, csp_instance: Type[Solver], assignments: dict[str, dict[str, Event]]) -> tuple[
        float, float]:
        # print(f'Constraint: {self.get_constraint_string()}  - sport: {self.get_sport().name}')
        sports = list(assignments.keys())

        current = 0
        max_possible = 0
        event_count = 0

        for sport_name in sports:
            assignment_by_sport = assignments[sport_name]
            assignments = list(assignment_by_sport.values())
            count = sum(event.venue.capacity for event in assignments)
            current += count
            sport = assignments[0].sport
            max_venue_capacity = max(venue.capacity for venue in sport.possible_venues)
            max_possible += len(assignments) * max_venue_capacity
            event_count += len(assignments)

        return current / event_count, current / max_possible


class AvgDistanceToTravel(OptionalConstraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "avg_distance_to_travel"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, csp_instance: Type[Solver], assignments: dict[str, dict[str, Event]]) -> tuple[
        float, float]:
        sports = list(assignments.keys())

        current = 0
        min_distance_total = 0
        event_count = 0

        for sport_name in sports:
            assignments = list(assignments[sport_name].values())
            if not ("distances_to_travel" in csp_instance.data):
                csp_instance.data["distances_to_travel"] = {}
            if not (sport_name in csp_instance.data["distances_to_travel"]):
                dist = pgeocode.GeoDistance('GB')
                distances_to_travel = {}
                accommodation = csp_instance.data["athletes_accommodation_postcode"]

                sports = [assignment.sport for assignment in assignments]
                sports_seen = []
                for sport in sports:
                    if sport in sports_seen:
                        continue
                    sports_seen.append(sport)
                    for venue in sport.possible_venues:
                        distances_to_travel[venue.name] = dist.query_postal_code(accommodation, venue.postcode)
                csp_instance.data["distances_to_travel"][sport_name] = distances_to_travel

            match_distances = []

            for event in assignments:
                match_distances.append(csp_instance.data["distances_to_travel"][sport_name][event.venue.name])

            # curr = sum(match_distances) / len(match_distances)
            current += sum(match_distances)

            min_distance = min(csp_instance.data["distances_to_travel"][sport_name].values())
            min_distance_total += min_distance * len(match_distances)
            event_count += len(match_distances)

        return current / event_count, round(min_distance_total / current, 6)


class AvgRestBetweenMatches(OptionalConstraint):
    def set_variables(self, val):
        self._variables = val

    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self._constraint_string = "avg_rest_between_matches"
        self._constraint_type = ConstraintType.ALL
        self._variables = variables
        self._sport = sport
        self._params = params

    def eval_constraint(self, csp_instance: Solver, assignments: dict[str, dict[str, Event]]) -> tuple[float, float]:
        def get_avg_rest(rest_dict) -> tuple[float, float]:
            rest_team_list = []
            rest_dict = {k: v for k, v in rest_dict.items() if len(rest_dict[k]) > 1}
            if rest_dict == {}:
                return 0
            for temp_team in rest_dict:
                count = 0
                for temp_match in range(len(rest_dict[temp_team]) - 1):
                    count += rest_dict[temp_team][temp_match + 1] - rest_dict[temp_team][temp_match]
                rest_team_list.append(count / (len(rest_dict[temp_team]) - 1))

            return sum(rest_team_list) / len(rest_team_list), len(rest_team_list)

        current = 0
        max_rest_total = 0
        team_count = 0

        sports = list(assignments.keys())

        for sport_name in sports:
            assignments = list(assignments[sport_name].values())
            rest_between_matches: dict[str, list[int]] = {}
            for event in assignments:
                for team in event.teams_involved:
                    if not (team in rest_between_matches):
                        rest_between_matches[team] = [event.day]
                    else:
                        insort(rest_between_matches[team], event.day)

            curr, num_teams = get_avg_rest(rest_between_matches)

            matches_to_win = math.ceil(
                math.log(assignments[0].sport.num_teams, assignments[0].sport.num_teams_per_game))
            days_available = csp_instance.data[sport_name]["max_finish_day"] - csp_instance.data[sport_name][
                "min_start_day"] + 1

            optimal = days_available / (matches_to_win - 1)
            # print()
            # print(sport_name)
            # print(curr, num_teams)
            # print(optimal, num_teams)

            # num_teams = len(list(rest_between_matches.keys()))
            current += curr * num_teams
            max_rest_total += optimal * num_teams
            team_count += num_teams

        # print(f'\neval score: {current / max_rest_total}')
        return current / team_count, current / max_rest_total


# Helper functions
def get_optional_constraint_from_string(string: str):
    if not (string in optional_constraints_list):
        handle_error("Constraint does not exist: " + string)
    return optional_constraints_list[string]


def get_optional_constraint_string_from_lambda(function) -> str:
    for key in optional_constraints_list:
        if optional_constraints_list[key].function == function:
            return key

    handle_error("Constraint does not exist")


# Constraint list
optional_constraints_list = {
    "max_matches_per_day": MaxMatchesPerDayHeuristic,
    "avg_capacity": AvgCapacityHeuristic,
    "avg_distance_to_travel": AvgDistanceToTravel,
    "avg_rest_between_matches": AvgRestBetweenMatches,
    # "maximise_sport_specific_constraints": MaximiseSportSpecificConstraints
}


def get_inequality_operator_from_input(inequality: str):
    if inequality == "MAXIMISE":
        return operator.gt
    elif inequality == "MINIMISE":
        return operator.lt
    else:
        handle_error("Inequality given is: \n" + inequality + "\nInequality operator does not exist")

import math
from abc import ABC, abstractmethod
from bisect import insort
import operator
from typing import Type

import pgeocode

from src.constraints.constraint import ConstraintType, Constraint
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import flatten_events_by_sport_to_list, remove_scores_from_dict
from src.schedulers.solver import Solver
from src.sports.sport import Sport


class OptionalConstraint(ABC):
    def variables(self):
        raise NotImplementedError()

    def sport(self):
        raise NotImplementedError()

    def params(self):
        raise NotImplementedError()

    def constraint_string(self):
        raise NotImplementedError()

    def constraint_type(self):
        raise NotImplementedError()

    @abstractmethod
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        pass

    @abstractmethod
    def solve(self, csp_instance, variables):
        pass

    def __str__(self) -> str:
        return f"""{{
            constraint: {self.constraint_string},
            variables: {self.variables},
            sport: {self.sport},
            constraint_type: {self.constraint_type}
        \n}}"""

    def __eq__(self, other):
        return self.constraint_string == other.constraint.string_name and self.variables == other.variables

    def __hash__(self):
        hash((self.constraint_string, self.sport, self.constraint_type, self.params, self.variables))


def take_average_of_heuristics_across_all_sports(csp_instance: Solver,
                                                 assignments_by_sport: dict[str, dict[str, Event]],
                                                 heuristic: Type[OptionalConstraint]) -> float:
    heuristic_count = 0
    sport_count = 0
    for sport in assignments_by_sport:
        _, score = heuristic.solve(csp_instance, assignments_by_sport[sport])
        heuristic_count += score
        sport_count += 1
    return heuristic_count / sport_count


# Optional Constraint Definitions
class MaxMatchesPerDayHeuristic(OptionalConstraint):
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self.constraint_string = "max_matches_per_day_heuristic"
        self.constraint_type = ConstraintType.ALL
        self.variables = variables
        self.sport = sport
        self.params = params

    def solve(self, csp_instance: Solver, assignments: dict[str, tuple[float, dict[str, Event]]]) -> \
            tuple[
                float, float]:
        assignments_heuristic = remove_scores_from_dict(assignments)
        events = flatten_events_by_sport_to_list(assignments_heuristic)

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


class MaximiseSportSpecificConstraints(OptionalConstraint):
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self.constraint_string = "maximise_sport_specific_constraints"
        self.constraint_type = ConstraintType.ALL
        self.variables = variables
        self.sport = sport
        self.params = params

    def solve(self, csp_instance: Type[Solver], assignments: dict[str, Event]) -> tuple[float, float]:
        curr = sum(assignments[sport][0] for sport in assignments)

        optimal = 0
        try:
            for sport in csp_instance.queue.variables:
                optimal += max(option[0] for option in sport.domain)
        except:
            handle_error("Non-CSOPSolver solver used when CSOPSolver was expected")

        score = (curr + sum(max(option[0] for option in sport.domain) for sport in csp_instance.queue.variables if
                            not (sport.variable in assignments))) / optimal
        return curr, score


class AvgCapacityHeuristic(OptionalConstraint):
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self.constraint_string = "avg_capacity_heuristic"
        self.constraint_type = ConstraintType.ALL
        self.variables = variables
        self.sport = sport
        self.params = params

    def solve(self, csp_instance: Type[Solver], assignments: dict[str, Event]) -> tuple[float, float]:
        assignments = list(assignments.values())
        count = sum(event.venue.capacity for event in assignments)
        curr = count / len(assignments)
        sport = assignments[0].sport
        max_venue_capacity = max(venue.capacity for venue in sport.possible_venues)

        return curr, curr / max_venue_capacity


class AvgDistanceToTravel(OptionalConstraint):
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self.constraint_string = "avg_distance_to_travel"
        self.constraint_type = ConstraintType.ALL
        self.variables = variables
        self.sport = sport
        self.params = params

    def solve(self, csp_instance: Type[Solver], assignments: dict[str, Event]) -> tuple[float, float]:
        assignments = list(assignments.values())
        sport_name = assignments[0].sport.name
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

        curr = sum(match_distances) / len(match_distances)

        min_distance = min(csp_instance.data["distances_to_travel"][sport_name].values())

        return curr, min_distance / curr


class AvgRestBetweenMatches(OptionalConstraint):
    def __init__(self, variables=None, sport: Sport = None, params: dict = None):
        self.constraint_string = "avg_rest_between_matches"
        self.constraint_type = ConstraintType.ALL
        self.variables = variables
        self.sport = sport
        self.params = params

    def solve(self, csp_instance: Solver, assignments: dict[str, Event]) -> tuple[float, float]:
        assignments = list(assignments.values())
        rest_between_matches: dict[str, list[int]] = {}
        sport_name = assignments[0].sport.name
        for event in assignments:
            for team in event.teams_involved:
                if not (team in rest_between_matches):
                    rest_between_matches[team] = [event.day]
                else:
                    insort(rest_between_matches[team], event.day)

        def get_avg_rest(rest_dict) -> float:
            rest_team_list = []
            rest_dict = {k: v for k, v in rest_dict.items() if len(rest_dict[k]) > 1}
            if rest_dict == {}:
                return 0
            for temp_team in rest_dict:
                count = 0
                for temp_match in range(len(rest_dict[temp_team]) - 1):
                    count += rest_dict[temp_team][temp_match + 1] - rest_dict[temp_team][temp_match]
                rest_team_list.append(count / (len(rest_dict[temp_team]) - 1))

            return sum(rest_team_list) / len(rest_team_list)

        curr = get_avg_rest(rest_between_matches)

        teams = assignments[0].sport.teams
        matches_to_win = math.ceil(math.log2(assignments[0].sport.num_teams))
        days_available = csp_instance.data[sport_name]["max_finish_day"] - csp_instance.data[sport_name][
            "min_start_day"] + 1

        optimal = days_available / (matches_to_win - 1)

        if "solver" in csp_instance.data and csp_instance.data["solver"] == "GeneticAlgorithmSolver":
            return curr, curr / optimal

        for team in teams:
            if not (team in rest_between_matches):
                rest_days = days_available / (matches_to_win - 1) if matches_to_win > 1 else days_available
                rest_between_matches[team] = [math.ceil(i * rest_days) for i in range(matches_to_win)]
            else:
                games_played = len(rest_between_matches[team])
                rest_days = (csp_instance.data[sport_name]["max_finish_day"] - rest_between_matches[team][-1] + 1) / (
                        matches_to_win - games_played - 1) if matches_to_win - games_played > 1 else \
                    csp_instance.data[sport_name]["max_finish_day"] - rest_between_matches[team][-1] + 1
                for match in range(matches_to_win - len(rest_between_matches[team])):
                    rest_between_matches[team].append(rest_between_matches[team][-1] + match * rest_days)

        avg_rest = get_avg_rest(rest_between_matches)

        return curr, curr / optimal


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
    "maximise_sport_specific_constraints": MaximiseSportSpecificConstraints
}


def get_inequality_operator_from_input(inequality: str):
    if inequality == "MAXIMISE":
        return operator.gt
    elif inequality == "MINIMISE":
        return operator.lt
    else:
        handle_error("Inequality given is: \n" + inequality + "\nInequality operator does not exist")

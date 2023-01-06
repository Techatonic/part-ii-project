import math
from bisect import insort
from enum import Enum
import operator

import pgeocode

from src.constraints.constraint import ConstraintFunction, ConstraintType
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import reformat_assignments, flatten_events_by_sport_to_list
from src.solvers.solver import Solver


# Optional Constraint Definitions
def max_matches_per_day_heuristic(csp_instance: Solver, *assignments: dict[str, tuple[float, dict[str, Event]]]) -> \
        tuple[
            float, float]:
    assignments_heuristic = reformat_assignments(assignments, dict)
    events = flatten_events_by_sport_to_list(assignments_heuristic)
    # print(events)
    num_events_to_add = csp_instance.data["num_total_events"] - len(events)

    def get_matches_per_day(temp_assignments: list[Event]):
        temp_assignments_by_day = {}
        for event in temp_assignments:
            if not (event.day in temp_assignments_by_day):
                temp_assignments_by_day[event.day] = 1
            else:
                temp_assignments_by_day[event.day] += 1
        return temp_assignments_by_day

    curr = max(get_matches_per_day(events).values())

    for index in range(num_events_to_add):
        new_assignment = events[0].__copy__()
        new_assignment.day = 1
        events.append(new_assignment)

    assignments_by_day = get_matches_per_day(events)

    optimal = math.ceil(
        csp_instance.data["num_total_events"] / csp_instance.data["tournament_length"])

    score = optimal / max(assignments_by_day.values())

    return score, curr


def maximise_sport_specific_constraints(csp_instance: Solver,
                                        *assignments: dict[str, tuple[float, dict[str, Event]]]) -> tuple[float, float]:
    assignments_by_sport = reformat_assignments(assignments, dict, True)
    # print(assignments_by_sport)
    curr = sum(assignments_by_sport[sport][0] for sport in assignments_by_sport)

    optimal = 0
    try:
        for sport in csp_instance.queue.variables:
            optimal += max(option[0] for option in sport.domain)
    except:
        handle_error("Non-CSOPSolver solver used when CSOPSolver was expected")

    score = (curr + sum(max(option[0] for option in sport.domain) for sport in csp_instance.queue.variables if
                        not (sport.variable in assignments_by_sport))) / optimal
    return score, curr


def avg_capacity_heuristic(csp_instance: Solver, *assignments: list[Event]) -> tuple[float, float]:
    assignments_list = reformat_assignments(assignments)
    count = sum(event.venue.capacity for event in assignments_list)
    curr = count / len(assignments_list)
    max_venue_capacity = max(venue.capacity for venue in csp_instance.data["venues"])
    heuristic_count = count + max_venue_capacity * (csp_instance.data["num_total_events"] - len(assignments_list))
    optimal = max_venue_capacity * csp_instance.data["num_total_events"]
    # print("Avg_capacity: ", heuristic_count / optimal)
    return curr, heuristic_count / optimal


def avg_distance_to_travel(csp_instance: Solver, *assignments: list[Event]) -> tuple[float, float]:
    if not ("distances_to_travel" in csp_instance.data):
        dist = pgeocode.GeoDistance('GB')
        distances_to_travel = {}
        accommodation = csp_instance.data["athletes_accommodation_postcode"]
        for venue in csp_instance.data["venues"]:
            distances_to_travel[venue.name] = dist.query_postal_code(accommodation, venue.postcode)
        csp_instance.data["distances_to_travel"] = distances_to_travel

    assignments = reformat_assignments(assignments)

    match_distances = []

    for event in assignments:
        match_distances.append(csp_instance.data["distances_to_travel"][event.venue.name])

    curr = sum(match_distances) / len(match_distances)

    # if len(assignments) == csp_instance.data["num_total_events"]:
    #
    # print(curr)
    # print(match_distances)
    # print()

    min_distance = min(csp_instance.data["distances_to_travel"].values())

    for new_event in range(csp_instance.data["num_total_events"] - len(match_distances)):
        match_distances.append(min_distance)

    avg_distance = sum(match_distances) / len(match_distances)

    optimal = min_distance  # best average is just the minimum distance for every event

    return curr, optimal / avg_distance


def avg_rest_between_matches(csp_instance: Solver, *assignments: list[Event]) -> tuple[float, float]:
    assignments = reformat_assignments(assignments)
    rest_between_matches: dict[str, list[int]] = {}
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
    days_available = csp_instance.data["max_finish_day"] - csp_instance.data["min_start_day"] + 1
    for team in teams:
        if not (team in rest_between_matches):
            rest_days = days_available / (matches_to_win - 1) if matches_to_win > 1 else days_available
            rest_between_matches[team] = [math.ceil(i * rest_days) for i in range(matches_to_win)]
        else:
            games_played = len(rest_between_matches[team])
            rest_days = (csp_instance.data["max_finish_day"] - rest_between_matches[team][-1] + 1) / (
                    matches_to_win - games_played - 1) if matches_to_win - games_played > 1 else csp_instance.data[
                                                                                                     "max_finish_day"] - \
                                                                                                 rest_between_matches[
                                                                                                     team][-1] + 1
            for match in range(matches_to_win - len(rest_between_matches[team])):
                rest_between_matches[team].append(rest_between_matches[team][-1] + match * rest_days)

    avg_rest = get_avg_rest(rest_between_matches)

    optimal = days_available / (matches_to_win - 1)

    return curr, avg_rest / optimal


# Helper functions
def get_optional_constraint_from_string(string: str) -> ConstraintFunction:
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
    "max_matches_per_day": ConstraintFunction("max_matches_per_day", max_matches_per_day_heuristic, ConstraintType.ALL),
    "avg_capacity": ConstraintFunction("avg_capacity", avg_capacity_heuristic, ConstraintType.ALL),
    "avg_distance_to_travel": ConstraintFunction("avg_distance_to_travel", avg_distance_to_travel, ConstraintType.ALL),
    "avg_rest_between_matches": ConstraintFunction("avg_rest_between_matches", avg_rest_between_matches,
                                                   ConstraintType.ALL),
    "maximise_sport_specific_constraints": ConstraintFunction("maximise_sport_specific_constraints",
                                                              maximise_sport_specific_constraints, ConstraintType.ALL)
}


def get_inequality_operator_from_input(inequality: str):
    if inequality == "MAXIMISE":
        return operator.gt
    elif inequality == "MINIMISE":
        return operator.lt
    else:
        handle_error("Inequality operator does not exist")

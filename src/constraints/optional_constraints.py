import math
from bisect import insort
import pgeocode

from src.constraints.constraint import ConstraintFunction, ConstraintType
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import convert_possible_tuple_to_list
from src.solvers.solver import Solver


# Optional Constraint Definitions
def max_matches_per_day_heuristic(csp_instance: Solver, *assignments: list[Event]) -> float:
    assignments_heuristic = convert_possible_tuple_to_list(assignments)
    num_events_to_add = csp_instance.data["num_total_events"] - len(assignments)
    for index in range(num_events_to_add):
        new_assignment = assignments_heuristic[0].__copy__()
        new_assignment.day = 1
        assignments_heuristic.append(new_assignment)

    assignments_by_day = {}
    for event in assignments_heuristic:
        if not (event.day in assignments_by_day):
            assignments_by_day[event.day] = 1
        else:
            assignments_by_day[event.day] += 1

    optimal = math.ceil(
        csp_instance.data["num_total_events"] / csp_instance.data["num_available_days"])
    return optimal / max(assignments_by_day.values())


def avg_capacity_heuristic(csp_instance: Solver, *assignments: list[Event]) -> float:
    assignments_list = convert_possible_tuple_to_list(assignments)
    count = sum(event.venue.capacity for event in assignments_list)
    max_venue_capacity = max(venue.capacity for venue in csp_instance.data["venues"])
    heuristic_count = count + max_venue_capacity * (csp_instance.data["num_total_events"] - len(assignments_list))
    optimal = max_venue_capacity * csp_instance.data["num_total_events"]
    # print("Avg_capacity: ", heuristic_count / optimal)
    return heuristic_count / optimal


def avg_distance_to_travel(csp_instance: Solver, *assignments: list[Event]) -> float:
    if not ("distances_to_travel" in csp_instance.data):
        dist = pgeocode.GeoDistance('GB')
        distances_to_travel = {}
        accommodation = csp_instance.data["athletes_accommodation_postcode"]
        for venue in csp_instance.data["venues"]:
            distances_to_travel[venue.name] = dist.query_postal_code(accommodation, venue.postcode)
        csp_instance.data["distances_to_travel"] = distances_to_travel

    assignments = convert_possible_tuple_to_list(assignments)

    match_distances = []

    for event in assignments:
        match_distances.append(csp_instance.data["distances_to_travel"][event.venue.name])

    min_distance = min(csp_instance.data["distances_to_travel"].values())

    for new_event in range(csp_instance.data["num_total_events"] - len(match_distances)):
        match_distances.append(min_distance)

    avg_distance = sum(match_distances) / len(match_distances)

    optimal = min_distance  # best average is just the minimum distance for every event

    return optimal / avg_distance


def avg_rest_between_matches(csp_instance: Solver, *assignments: list[Event]) -> float:
    assignments = convert_possible_tuple_to_list(assignments)
    rest_between_matches = {}
    for event in assignments:
        for team in event.teams_involved:
            if not (team in rest_between_matches):
                rest_between_matches[team] = [event.day]
            else:
                insort(rest_between_matches[team], event.day)

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

    avg_rest = []
    for team in rest_between_matches:
        count = 0
        for match in range(len(rest_between_matches[team]) - 1):
            count += rest_between_matches[team][match + 1] - rest_between_matches[team][match]
        avg_rest.append(count / (len(rest_between_matches[team]) - 1))

    avg_rest = sum(avg_rest) / len(avg_rest)

    optimal = days_available / (matches_to_win - 1)

    return avg_rest / optimal


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
                                                   ConstraintType.ALL)
}

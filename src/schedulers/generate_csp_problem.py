import math
import random
from typing import Type

import numpy as np

from src.helper.handle_error import handle_error
from src.events.event import Event
from src.rounds.knockout_rounds import Round, generate_round_order
from src.schedulers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


def generate_csp_problem(solver: Type[Solver], data: dict, forward_check: bool, sport: Sport) -> Solver:
    csp_problem = solver(data, forward_check=forward_check)

    sport_name: str = sport.name
    venues: list[Venue] = sport.possible_venues
    min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
    max_finish_day: int = data[
        "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
    round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

    for optional_constraint in sport.constraints["optional"]:
        csp_problem.add_optional_constraint(optional_constraint, sport,
                                            params=sport.constraints["optional"][optional_constraint])

    variable_list = []
    match_num = 1
    matches = []
    for i in range(sport.num_teams // sport.num_teams_per_game):
        matches.append(
            [sport.teams[x] for x in range(sport.num_teams_per_game * i, sport.num_teams_per_game * (i + 1))])

    min_starts = [min_start_day]
    max_finishes = [max_finish_day]
    if 'max_matches_per_day' in sport.constraints:
        max_per_day = min(sum(venue.max_matches_per_day for venue in venues),
                          sport.constraints['max_matches_per_day']['max_matches_per_day'])
    else:
        max_per_day = sum(venue.max_matches_per_day for venue in venues)

    for _round in range(1, len(round_order)):
        num_matches = len(matches) / 2 ** (round_order[0].round_index - round_order[_round - 1].round_index)
        min_starts.append(min_starts[_round - 1] + max(math.ceil(num_matches / max_per_day),
                                                       sport.constraints['required']['team_time_between_matches'][
                                                           'min_time_between_matches']))

    for _round in range(len(round_order) - 2, -1, -1):
        num_matches = len(matches) / 2 ** (round_order[0].round_index - round_order[_round + 1].round_index)
        max_finishes.insert(0, max_finishes[0] - max(math.ceil(num_matches / max_per_day),
                                                     sport.constraints['required']['team_time_between_matches'][
                                                         'min_time_between_matches']))

    for event_round in round_order:
        if round_order.index(event_round) > 0:
            matches = [x + y for x, y in zip(matches[0::2], matches[1::2])]
        for match in matches:
            options = []
            specific_min_start_day = min_starts[round_order.index(event_round)]
            specific_max_finish_day = max_finishes[round_order.index(event_round)]

            if specific_min_start_day > specific_max_finish_day and len(round_order) > 1:
                handle_error("Insufficient number of days given for sport: ", sport.name)
            if specific_max_finish_day - specific_min_start_day + 1 < len(matches) / max_per_day:
                handle_error("Insufficient number of days given for sport: ", sport.name)
            day_order = list(range(specific_min_start_day, specific_max_finish_day + 1))
            event_id = sport.name + "_" + str(match_num)
            for venue in venues:
                min_start_time = max(sport.min_start_time, venue.min_start_time)
                max_finish_time = min(sport.max_finish_time, venue.max_finish_time)
                if "venue_time_between_matches" in sport.constraints['required']:
                    time_order = [int(x) for x in
                                  np.arange(min_start_time, math.ceil(max_finish_time - sport.match_duration) + 1,
                                            max(sport.constraints['required'][
                                                    'venue_time_between_matches'][
                                                    'min_time_between_matches'], 1))]
                else:
                    time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration) + 1))
                for time in time_order:
                    for day in day_order:
                        options.append(Event(sport, event_id, venue=venue, event_round=event_round,
                                             day=day, start_time=time, duration=sport.match_duration,
                                             teams_involved=match))

            random.shuffle(options)

            csp_problem.add_variable(sport_name + "_" + str(match_num), options)
            variable_list.append(sport_name + "_" + str(match_num))
            match_num += 1

    csp_problem.data["num_total_events"] = len(variable_list)

    for sport_specific_constraint in sport.constraints["required"]:
        csp_problem.add_constraint(sport_specific_constraint, sport=sport,
                                   params=sport.constraints["required"][sport_specific_constraint])
    for optional_constraint in sport.constraints["optional"]:
        csp_problem.add_optional_constraint(optional_constraint,
                                            params=sport.constraints["optional"][
                                                optional_constraint])

    return csp_problem

import math
import random
from typing import Type

from src.constraints.constraint import ConstraintFunction, get_constraint_from_string
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.rounds.knockout_rounds import Round, generate_round_order
from src.schedulers.solvers.solver import Solver
from src.venues.venue import Venue


def generate_csp_problem(solver: Type[Solver], data: dict, forward_check: bool) -> Solver:
    csp_problem = solver(data, forward_check=forward_check)

    sport = data["sport"]
    sport_name: str = sport.name
    venues: list[Venue] = sport.possible_venues
    min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
    max_finish_day: int = data[
        "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
    round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

    for optional_constraint in data["sport"].constraints["optional"]:
        csp_problem.add_optional_constraint(optional_constraint, sport,
                                            params=sport.constraints["optional"][optional_constraint])

    variable_list = []
    match_num = 1
    matches = [[sport.teams[2 * i], sport.teams[2 * i + 1]] for i in range(sport.num_teams // 2)]
    for event_round in round_order:
        if round_order.index(event_round) > 0:
            matches = [x + y for x, y in zip(matches[0::2], matches[1::2])]
        for match in matches:
            options = []
            # Shuffle venues, days and times
            specific_min_start_day = min_start_day + \
                                     sport.constraints["required"]["team_time_between_matches"][
                                         "min_time_between_matches"] * (
                                             round_order[0].round_index - event_round.round_index)
            specific_max_finish_day = max_finish_day - \
                                      sport.constraints["required"]["team_time_between_matches"][
                                          "min_time_between_matches"] * event_round.round_index
            if specific_min_start_day >= specific_max_finish_day and len(round_order) > 1:
                handle_error("Insufficient number of days given for sport: ", sport.name)
            day_order = list(range(specific_min_start_day, specific_max_finish_day + 1))

            for venue in venues:
                min_start_time = max(sport.min_start_time, venue.min_start_time)
                max_finish_time = min(sport.max_finish_time, venue.max_finish_time)
                time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration)))
                for time in time_order:
                    for day in day_order:
                        options.append(Event(sport, match_num, venue=venue, event_round=event_round,
                                             day=day, start_time=time, duration=sport.match_duration,
                                             teams_involved=match))

            random.shuffle(options)

            csp_problem.add_variable(sport_name + "_" + str(match_num), options)
            variable_list.append(sport_name + "_" + str(match_num))
            match_num += 1

    csp_problem.data["num_total_events"] = len(variable_list)

    for sport_specific_constraint in sport.constraints["required"]:
        constraint: ConstraintFunction = get_constraint_from_string(sport_specific_constraint)
        # TODO This has been changed to make it so you just add the constraint, not the specific events involved.
        # TODO Fix the effects of this in other places, particularly with the constraint checker functionality
        csp_problem.add_constraint(constraint.string_name, sport=sport,
                                   params=sport.constraints["required"][sport_specific_constraint])

    return csp_problem

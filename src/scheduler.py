import math
import random
from typing import Type

from src.constraints.constraint import get_constraint_from_string, ConstraintType, ConstraintFunction, params
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.rounds.knockout_rounds import generate_round_order, Round
from src.solvers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


def solve(solver: Type[Solver], sports: list[Sport], tournament_length: int, general_constraints: list[str],
          forward_check: bool) -> dict[str, Event] | None:
    """
    Method to solve the CSP scheduling problem
    :param solver: Type[Solver]
    :param sports: List[Sport]
    :param tournament_length: int
    :param general_constraints: List[string]
    :param forward_check: bool
    :return result: List[Event] | None
    """

    total_events: list[dict[str, Event]] = []

    for sport in sports:
        csp_problem = solver(forward_check=forward_check)

        sport_name: str = sport.name
        venues: list[Venue] = sport.possible_venues
        min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
        max_finish_day: int = tournament_length if sport.max_finish_day is None else sport.max_finish_day

        # Define the variables
        # Add matches
        round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

        variable_list = []
        match_num = 1
        matches = [[sport.teams[2 * i], sport.teams[2 * i + 1]] for i in range(sport.num_teams // 2)]
        for event_round in round_order:
            if round_order.index(event_round) > 0:
                matches = [x + y for x, y in zip(matches[0::2], matches[1::2])]
            for match in matches:
                options = []
                # Shuffle venues, days and times
                random.shuffle(venues)
                specific_min_start_day = min_start_day + params[sport.name]["team_time_between_matches"][
                    "min_time_between_matches"] * (round_order[0].round_index - event_round.round_index)
                specific_max_finish_day = max_finish_day - params[sport.name]["team_time_between_matches"][
                    "min_time_between_matches"] * event_round.round_index
                if specific_min_start_day >= specific_max_finish_day and len(round_order) > 1:
                    handle_error("Insufficient number of days given for sport: ", sport.name)
                day_order = list(range(specific_min_start_day, specific_max_finish_day + 1))
                random.shuffle(day_order)

                for venue in venues:
                    min_start_time = max(sport.min_start_time, venue.min_start_time)
                    max_finish_time = min(sport.max_finish_time, venue.max_finish_time)
                    time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration)))
                    random.shuffle(time_order)
                    for time in time_order:
                        for day in day_order:
                            options.append(Event(sport, match_num, venue=venue, event_round=event_round,
                                                 day=day, start_time=time, duration=sport.match_duration,
                                                 teams_involved=match))

                csp_problem.add_variable(sport_name + "_" + str(match_num), options)
                variable_list.append(sport_name + "_" + str(match_num))
                match_num += 1

        for sport_specific_constraint in sport.constraints:
            constraint: ConstraintFunction = get_constraint_from_string(sport_specific_constraint)
            if constraint.constraint_type == ConstraintType.UNARY:
                for event in variable_list:
                    csp_problem.add_constraint(constraint.string_name, [event], sport)
            elif constraint.constraint_type == ConstraintType.BINARY:
                for event_1 in range(len(variable_list)):
                    for event_2 in range(event_1 + 1, len(variable_list)):
                        csp_problem.add_constraint(constraint.string_name,
                                                   [variable_list[event_1], variable_list[event_2]], sport)
            else:
                csp_problem.add_constraint(constraint.string_name, sport=sport)

        result: dict[str, Event] = csp_problem.solve()
        # print("Done: " + sport.name)
        if result is None:
            return None
        # Add all sport-specific events to list of all events
        total_events.append(result)

    # print("Done individual sports. Beginning all sports")

    # Run CSP across all events in all sports
    # total_csp_problem = solver(forward_check)
    # variable_list = []
    # # print("Add variables")
    # for sport_events in total_events:
    #     for sport_event in sport_events:
    #         options = []
    #         min_start_time = max(sport_events[sport_event].sport.min_start_time,
    #                              sport_events[sport_event].venue.min_start_time)
    #         max_finish_time = min(sport_events[sport_event].sport.max_finish_time,
    #                               sport_events[sport_event].venue.max_finish_time)
    #         for time in range(min_start_time,
    #                           max_finish_time - math.ceil(sport_events[sport_event].sport.match_duration) + 1):
    #             event_temp = sport_events[sport_event].__copy__()
    #             event_temp.start_time = time
    #             options.append(event_temp)
    #         total_csp_problem.add_variable(sport_events[sport_event].event_id, options)
    #         variable_list.append(sport_events[sport_event].event_id)
    #
    # # Add total sport constraints
    # for general_constraint in general_constraints:
    #     constraint = get_constraint_from_string(general_constraint)
    #     if constraint.constraint_type == ConstraintType.UNARY:
    #         for event in variable_list:
    #             total_csp_problem.add_constraint(constraint.string_name, [event])
    #     elif constraint.constraint_type == ConstraintType.BINARY:
    #         for event_1 in range(len(variable_list)):
    #             for event_2 in range(event_1 + 1, len(variable_list)):
    #                 total_csp_problem.add_constraint(constraint.string_name,
    #                                                  [variable_list[event_1], variable_list[event_2]])
    #     else:
    #         total_csp_problem.add_constraint(constraint.string_name)
    #
    # result: dict[str, Event] = total_csp_problem.solve()
    return total_events[0]

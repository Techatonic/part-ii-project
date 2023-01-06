import copy
import math
import random
import time
from typing import Type

from src.constraints.constraint import get_constraint_from_string, ConstraintFunction
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.rounds.knockout_rounds import generate_round_order, Round
from src.solvers.solver import Solver, SolverType
from src.sports.sport import Sport
from src.venues.venue import Venue


def solve(solver: Type[Solver], solver_type: SolverType, sports: list[Sport], data: dict,
          general_constraints: dict[str, dict],
          forward_check: bool) -> CompleteGames | None:
    """
    Method to solve the CSP scheduling problem
    :param solver: Type[Solver]
    :param solver_type: SolverType
    :param sports: List[Sport]
    :param data: dict
    :param general_constraints: List[string]
    :param forward_check: bool
    :return result: dict[str, Event] | None
    """

    total_events = {}

    num_results_to_collect = 10

    for sport in sports:
        sport_name: str = sport.name
        venues: list[Venue] = sport.possible_venues
        min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
        max_finish_day: int = data[
            "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
        round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

        csp_data = copy.deepcopy(data)
        csp_data.update({
            "domain_type": list[Event],
            "variable_type": Event,
            "sport": sport,
            "round_order": round_order,
            "venues": venues,
            "min_start_day": min_start_day,
            "max_finish_day": max_finish_day,
            "solver_type": solver_type,
            "num_results_to_collect": 1,
            "comparator": lambda self, other: self.domain[0].round.round_index > other.domain[0].round.round_index or
                                              self.domain[0].round.round_index == other.domain[0].round.round_index and
                                              len(self.domain) < len(other.domain),
            "sport_specific": True,
            "sports": [sport],
            "wait_time": 5
        })

        sport_results = []

        # Run num_results_to_collect CSPs
        for _ in range(num_results_to_collect):
            attempts = 5
            while True:
                csp_problem = solver(csp_data, forward_check=forward_check)

                for optional_constraint in sport.constraints["optional"]:
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
                        random.shuffle(venues)
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

                csp_problem.data["num_total_events"] = len(variable_list)

                for sport_specific_constraint in sport.constraints["required"]:
                    constraint: ConstraintFunction = get_constraint_from_string(sport_specific_constraint)
                    # TODO This has been changed to make it so you just add the constraint, not the specific events involved.
                    # TODO Fix the effects of this in other places, particularly with the constraint checker functionality
                    csp_problem.add_constraint(constraint.string_name, sport=sport,
                                               params=sport.constraints["required"][sport_specific_constraint])

                try:
                    result = csp_problem.solve()
                    if result is None:
                        return None
                    sport_results += result
                    break
                except TimeoutError:
                    attempts -= 1
                    print("Retrying")
                    if attempts == 0:
                        return None

        # Add all sport-specific events to list of all events
        total_events[sport.name] = sport_results

    if solver_type in [SolverType.PYTHON_CONSTRAINT_SOLVER, SolverType.CUSTOMISED_SOLVER]:
        complete_games = CompleteGames(data["tournament_length"], sports)
        for sport in total_events:
            for event in total_events[sport]:
                complete_games.add_event(total_events[sport][event])
        return complete_games

    # Assertion added in case other solvers are created later
    assert solver_type == SolverType.CSOP_SOLVER

    csp_data = copy.deepcopy(data)
    # print(total_events)
    csp_data.update({
        "domain_type": list[tuple[float, dict[str, Event]]],
        "variable_type": tuple[float, dict[str, Event]],
        "num_total_events": sum(len(total_events[sport][0][1]) for sport in total_events),
        "num_results_to_collect": 1,
        "comparator": lambda self, other: len(self.domain) < len(other.domain),
        "sport_specific": False,
        "sports": sports,
        "wait_time": 25
    })

    multisport_csp = solver(csp_data, forward_check)

    for sport_key in total_events:
        sorted_options_by_optimality = sorted(total_events[sport_key], key=lambda option: -option[0])
        # print(sorted_options_by_optimality)
        multisport_csp.add_variable(sport_key, sorted_options_by_optimality)

    for required_constraint in general_constraints["required"]:
        multisport_csp.add_constraint(required_constraint,
                                      params=general_constraints["required"][required_constraint])
    for optional_constraint in general_constraints["optional"]:
        multisport_csp.add_optional_constraint(optional_constraint,
                                               params=general_constraints["optional"][optional_constraint])

    multisport_csp.add_optional_constraint("maximise_sport_specific_constraints",
                                           params={"inequality": "MAXIMISE", "acceptable": 0})

    print("\n\n\n Doing joint one \n\n\n")

    try:
        result = multisport_csp.solve()[0][1]
        if result is None:
            print("No results")
            return None
        complete_games = CompleteGames(data["tournament_length"], sports)
        for sport in result:
            for event in result[sport][1]:
                complete_games.add_event(result[sport][1][event])
        return complete_games
    except TimeoutError:
        return None

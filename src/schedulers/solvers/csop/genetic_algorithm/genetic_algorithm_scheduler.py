import copy
import math
from abc import ABC
from typing import Type

from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.rounds.knockout_rounds import generate_round_order, Round
from src.scheduler import Scheduler
from src.schedulers.solvers.generate_csp_problem import generate_csp_problem
from src.schedulers.solvers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


class GeneticAlgorithmScheduler(Scheduler, ABC):

    def __init__(self, solver: Type[Solver], sports: dict[str, Sport], data: dict, forward_check: bool):
        """
        Class to solve the CSP scheduling problem
        :param solver: Type[Solver]
        :param sports: List[Sport]
        :param data: dict
        :param forward_check: bool
        :return result: dict[str, Event] | None
        """
        super().__init__(solver, sports, data, forward_check)

    def schedule_events(self) -> CompleteGames | None:

        total_events = {}
        csp_data = copy.deepcopy(self.data)

        for sport in self.sports:
            sport = self.sports[sport]
            venues: list[Venue] = sport.possible_venues
            min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
            max_finish_day: int = self.data[
                "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
            round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

            csp_data[sport.name] = {
                "domain_type": list[Event],
                "variable_type": Event,
                "sport": sport,
                "round_order": round_order,
                "venues": venues,
                "min_start_day": min_start_day,
                "max_finish_day": max_finish_day,
                "num_results_to_collect": 1,
                "comparator": lambda curr, other: curr.domain[0].round.round_index > other.domain[
                    0].round.round_index or
                                                  curr.domain[0].round.round_index == other.domain[
                                                      0].round.round_index and
                                                  len(curr.domain) < len(other.domain),
                "sport_specific": True,
                "sports": [sport],
                "wait_time": 5
            }

        multisport_csp = self.solver(csp_data, self.forward_check)

        for sport_name in self.sports:
            sport = self.sports[sport_name]
            match_num = 1
            matches = [[sport.teams[2 * i], sport.teams[2 * i + 1]] for i in range(sport.num_teams // 2)]
            round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))
            min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
            max_finish_day: int = csp_data[
                "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day

            for event_round in round_order:
                if round_order.index(event_round) > 0:
                    matches = [x + y for x, y in zip(matches[0::2], matches[1::2])]
                for match in matches:
                    options = []
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
                    event_id = sport.name + "_" + str(match_num)
                    for venue in sport.possible_venues:
                        min_start_time = max(sport.min_start_time, venue.min_start_time)
                        max_finish_time = min(sport.max_finish_time, venue.max_finish_time)
                        time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration)))
                        for time in time_order:
                            for day in day_order:
                                options.append(Event(sport, event_id, venue=venue, event_round=event_round,
                                                     day=day, start_time=time, duration=sport.match_duration,
                                                     teams_involved=match))

                    multisport_csp.add_variable(event_id, options)
                    match_num += 1

        try:
            result = multisport_csp.solve()
            eval_score = result[0][0]
            result = result[0][1]
            if result is None:
                print("No results")
                return None
            print(result)
            complete_games = CompleteGames(self.data["tournament_length"], self.sports, eval_score)
            for sport in result:
                for event in result[sport][1]:
                    complete_games.add_event(result[sport][1][event])
            return complete_games
        except TimeoutError:
            return None

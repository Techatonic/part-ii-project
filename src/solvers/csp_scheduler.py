import copy
from abc import ABC
from typing import Type

from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.rounds.knockout_rounds import generate_round_order, Round
from src.scheduler import Scheduler
from src.solvers.generate_csp_problem import generate_csp_problem
from src.solvers.solver import Solver, SolverType
from src.sports.sport import Sport
from src.venues.venue import Venue


class CSPScheduler(Scheduler, ABC):

    def __init__(self, solver: Type[Solver], solver_type: SolverType, sports: list[Sport], data: dict,
                 forward_check: bool):
        """
        Class to solve the CSP scheduling problem
        :param solver: Type[Solver]
        :param solver_type: SolverType
        :param sports: List[Sport]
        :param data: dict
        :param forward_check: bool
        :return result: dict[str, Event] | None
        """
        super().__init__(solver, solver_type, sports, data, forward_check)

    def schedule_events(self) -> CompleteGames | None:
        total_events = {}

        for sport in self.sports:
            venues: list[Venue] = sport.possible_venues
            min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
            max_finish_day: int = self.data[
                "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
            round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

            csp_data = copy.deepcopy(self.data)
            csp_data.update({
                "domain_type": list[Event],
                "variable_type": Event,
                "sport": sport,
                "round_order": round_order,
                "venues": venues,
                "min_start_day": min_start_day,
                "max_finish_day": max_finish_day,
                "solver_type": self.solver_type,
                "num_results_to_collect": 1,
                "comparator": lambda curr, other: curr.domain[0].round.round_index > other.domain[
                    0].round.round_index or
                                                  curr.domain[0].round.round_index == other.domain[
                                                      0].round.round_index and
                                                  len(curr.domain) < len(other.domain),
                "sport_specific": True,
                "sports": [sport],
                "wait_time": 5
            })

            # Run num_results_to_collect CSPs
            csp_problem = generate_csp_problem(self.solver, csp_data, self.forward_check)

            result = csp_problem.solve()
            if result is None:
                return None

            # Add all sport-specific events to list of all events
            total_events[sport.name] = result

        complete_games = CompleteGames(self.data["tournament_length"], self.sports)
        for sport in total_events:
            for event in total_events[sport]:
                # print(event)
                # print(total_events[sport])
                complete_games.add_event(total_events[sport][event])
        return complete_games

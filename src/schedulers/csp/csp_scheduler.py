import copy
from abc import ABC
from typing import Type

from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.helper.helper import calculate_fitness
from src.rounds.knockout_rounds import generate_knockout_round_order, KnockoutRound
from src.schedulers.scheduler import Scheduler
from src.schedulers.generate_csp_problem import generate_csp_problem
from src.schedulers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


class CSPScheduler(Scheduler, ABC):
    def __init__(
        self,
        solver: Type[Solver],
        sports: dict[str, Sport],
        data: dict,
        forward_check: bool,
    ):
        """
        Class to solve the CSP scheduling problem
        :param solver: Type[Solver]
        :param sports: List[Sport]
        :param data: dict
        :param forward_check: bool
        :return result: dict[str, Event] | None
        """
        self.constraints = []
        self.optional_constraints = []
        super().__init__(solver, sports, data, forward_check)

    def schedule_events(self) -> CompleteGames | dict[str, dict[str, Event]] | None:
        total_events = {}

        for sport in self.sports:
            print(f"Scheduling: {sport}")
            sport = self.sports[sport]
            venues: list[Venue] = sport.possible_venues
            min_start_day: int = (
                0 if sport.min_start_day is None else sport.min_start_day
            )
            max_finish_day: int = (
                self.data["tournament_length"]
                if sport.max_finish_day is None
                else sport.max_finish_day
            )
            round_order: list[KnockoutRound] = list(
                reversed(
                    generate_knockout_round_order(
                        sport.num_teams, sport.num_teams_per_game, sport.group_stage
                    )
                )
            )

            self.data[sport.name] = {
                "domain_type": list[Event],
                "variable_type": Event,
                "sport": sport,
                "round_order": round_order,
                "venues": venues,
                "min_start_day": min_start_day,
                "max_finish_day": max_finish_day,
                "num_results_to_collect": 1,
                "sport_specific": True,
                "sports": [sport],
                "wait_time": 5,
            }
            csp_data = copy.deepcopy(self.data)
            csp_data["comparator"] = (
                lambda curr, other: curr.domain[0].round.round_index
                > other.domain[0].round.round_index
                or curr.domain[0].round.round_index == other.domain[0].round.round_index
                and len(curr.domain) < len(other.domain)
                or curr.domain[0].round.round_index == other.domain[0].round.round_index
                and len(curr.domain) == len(other.domain)
                and curr.variable < other.variable
            )

            csp_problem = generate_csp_problem(
                self.solver, csp_data, self.forward_check, sport
            )
            self.constraints += csp_problem.constraints
            self.optional_constraints += csp_problem.optional_constraints

            result = csp_problem.solve()
            if result is None:
                return None

            # Add all sport-specific events to list of all events
            total_events[sport.name] = result

        eval_score = calculate_fitness(
            total_events, self.constraints, self.optional_constraints, self, False
        )
        complete_games = CompleteGames(
            self.data["tournament_length"], self.sports, eval_score=eval_score
        )

        for sport in total_events:
            for event in total_events[sport]:
                complete_games.add_event(total_events[sport][event])
        return complete_games

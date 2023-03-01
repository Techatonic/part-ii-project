import copy
from abc import ABC
from typing import Type

from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.rounds.knockout_rounds import generate_round_order, Round
from src.scheduler import Scheduler
from src.schedulers.solvers.generate_csp_problem import generate_csp_problem
from src.schedulers.solvers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


class CSOPScheduler(Scheduler, ABC):

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

        num_results_to_collect = 10

        for sport in self.sports:
            sport = self.sports[sport]
            venues: list[Venue] = sport.possible_venues
            min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
            max_finish_day: int = self.data[
                "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
            round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

            csp_data = copy.deepcopy(self.data)
            csp_data[sport.name] = {
                "sport": sport,
                "round_order": round_order,
                "venues": venues,
                "min_start_day": min_start_day,
                "max_finish_day": max_finish_day,
                "sport_specific": True,
                "sports": [sport],
            }
            csp_data.update({
                "comparator": lambda curr, other: curr.domain[0].round.round_index > other.domain[
                    0].round.round_index or curr.domain[0].round.round_index == other.domain[
                                                      0].round.round_index and len(
                    curr.domain) < len(other.domain),
                "num_results_to_collect": 1,
                "wait_time": 5,
                "domain_type": list[Event],
                "variable_type": Event,
            })

            sport_results = []

            # Run num_results_to_collect CSPs
            for _ in range(num_results_to_collect):
                attempts = 5
                while True:
                    csp_problem = generate_csp_problem(self.solver, csp_data, self.forward_check, sport)
                    csp_data[sport.name]["num_total_events"] = len(csp_problem.get_variables())
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

        csp_data = copy.deepcopy(self.data)
        # print(total_events)
        csp_data.update({
            "domain_type": list[tuple[float, dict[str, Event]]],
            "variable_type": tuple[float, dict[str, Event]],
            "num_total_events": sum(len(total_events[sport][0][1]) for sport in total_events),
            "num_results_to_collect": 1,
            "comparator": lambda curr, other: len(curr.domain) < len(other.domain),
            "sport_specific": False,
            "sports": self.sports,
            "wait_time": 25
        })

        multisport_csp = self.solver(csp_data, self.forward_check)

        for sport_key in total_events:
            sorted_options_by_optimality = sorted(total_events[sport_key], key=lambda option: -option[0])
            # print(sorted_options_by_optimality)
            multisport_csp.add_variable(sport_key, sorted_options_by_optimality)

        for required_constraint in self.data["general_constraints"]["required"]:
            multisport_csp.add_constraint(required_constraint,
                                          params=self.data["general_constraints"]["required"][required_constraint])
        for optional_constraint in self.data["general_constraints"]["optional"]:
            multisport_csp.add_optional_constraint(optional_constraint,
                                                   params=self.data["general_constraints"]["optional"][
                                                       optional_constraint], sport=None)

        multisport_csp.add_optional_constraint("maximise_sport_specific_constraints",
                                               params={"inequality": "MAXIMISE", "acceptable": 0})

        try:
            result = multisport_csp.solve()
            eval_score = result[0][0]
            result = result[0][1]
            if result is None:
                print("No results")
                return None
            complete_games = CompleteGames(self.data["tournament_length"], self.sports, eval_score)
            for sport in result:
                for event in result[sport][1]:
                    complete_games.add_event(result[sport][1][event])
            return complete_games
        except TimeoutError:
            return None

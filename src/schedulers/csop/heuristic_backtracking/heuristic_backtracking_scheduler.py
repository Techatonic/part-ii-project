import copy
from abc import ABC
from typing import Type

from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.helper.helper import calculate_fitness, widen_events_to_events_by_sport, flatten_events_by_sport_to_dict, \
    remove_scores_from_dict
from src.rounds.knockout_rounds import generate_round_order, Round
from src.schedulers.csp.csp_solver import CSPSolver
from src.schedulers.scheduler import Scheduler
from src.schedulers.generate_csp_problem import generate_csp_problem
from src.schedulers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


class HeuristicBacktrackingScheduler(Scheduler, ABC):

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
        num_total_events = {}

        most_recent_csp = None

        sport_specific_data = {}

        for sport in self.sports:
            sport = self.sports[sport]
            venues: list[Venue] = sport.possible_venues
            min_start_day: int = 0 if sport.min_start_day is None else sport.min_start_day
            max_finish_day: int = self.data[
                "tournament_length"] if sport.max_finish_day is None else sport.max_finish_day
            round_order: list[Round] = list(reversed(generate_round_order(sport.num_teams, sport.num_teams_per_game)))

            csp_data = copy.deepcopy(self.data)
            sport_specific_data[sport.name] = {
                "sport": sport,
                "round_order": round_order,
                "venues": venues,
                "min_start_day": min_start_day,
                "max_finish_day": max_finish_day,
                "sport_specific": True,
                "sports": [sport],
                "optional_constraints": []
            }
            csp_data[sport.name] = sport_specific_data[sport.name]
            csp_data.update({
                "comparator": lambda curr, other: curr.domain[0].round.round_index > other.domain[
                    0].round.round_index or curr.domain[0].round.round_index == other.domain[
                                                      0].round.round_index and len(
                    curr.domain) < len(other.domain),
                "wait_time": 5,
                "domain_type": list[Event],
                "variable_type": Event,
            })

            sport_results = []

            # Run num_results_to_collect CSPs
            for _ in range(self.data['num_results_to_collect']):
                attempts = 5
                while True:
                    csp_problem = generate_csp_problem(CSPSolver, csp_data, self.forward_check, sport)
                    most_recent_csp = csp_problem
                    csp_data[sport.name]["num_total_events"] = len(csp_problem.get_variables())
                    num_total_events[sport.name] = len(csp_problem.get_variables())
                    for optional_constraint in csp_problem.optional_constraints:
                        sport_specific_data[sport.name]['optional_constraints'].append(optional_constraint)
                    try:
                        result = csp_problem.solve()
                        fitness = calculate_fitness(widen_events_to_events_by_sport(result), csp_problem.constraints,
                                                    csp_problem.optional_constraints, csp_problem)
                        if result is None:
                            return None
                        sport_results.append((fitness, result))
                        break
                    except TimeoutError:
                        attempts -= 1
                        print("Retrying")
                        if attempts == 0:
                            return None

            # Add all sport-specific events to list of all events
            total_events[sport.name] = sport_results

        csp_data = copy.deepcopy(self.data)

        num_total_events = sum(num_total_events.values())

        csp_data.update({
            "domain_type": list[tuple[float, dict[str, Event]]],
            "variable_type": tuple[float, dict[str, Event]],
            "num_total_events": num_total_events,
            "comparator": lambda curr, other: len(curr.domain) < len(other.domain),
            "sport_specific": False,
            "sports": self.sports,
            "wait_time": 25,
        })

        csp_data.update(sport_specific_data)

        while len(total_events) > 1:
            results = []
            multisport_csp = self.solver(csp_data, self.forward_check)
            sport_1 = list(total_events.keys())[0]
            sport_2 = list(total_events.keys())[1]

            for sport_key in [sport_1, sport_2]:
                sorted_options_by_optimality = sorted(total_events[sport_key], key=lambda option: option[0],
                                                      reverse=True)
                multisport_csp.add_variable(sport_key, sorted_options_by_optimality)

            for required_constraint in self.data["general_constraints"]["required"]:
                multisport_csp.add_constraint(required_constraint,
                                              params=self.data["general_constraints"]["required"][required_constraint])

            for optional_constraint in self.data["general_constraints"]["optional"]:
                multisport_csp.add_optional_constraint(optional_constraint,
                                                       params=self.data["general_constraints"]["optional"][
                                                           optional_constraint], sport=None)

            result = multisport_csp.solve()
            if result is None:
                return None
            del total_events[sport_1]
            del total_events[sport_2]

            for individual_result in range(len(result)):
                events = result[individual_result][1]
                events = remove_scores_from_dict(events)
                eval_score = calculate_fitness(events, multisport_csp.constraints,
                                               multisport_csp.optional_constraints, multisport_csp)
                events = flatten_events_by_sport_to_dict(events)
                result[individual_result] = (eval_score, events)
            total_events[sport_1 + "#" + sport_2] = result
            most_recent_csp = multisport_csp

        result = list(total_events.values())[0]
        result = sorted(result, key=lambda option: -option[0])[0]

        result = result[1]
        result = widen_events_to_events_by_sport(result)

        eval_score = calculate_fitness(result, most_recent_csp.constraints, most_recent_csp.optional_constraints,
                                       most_recent_csp)

        complete_games = CompleteGames(self.data["tournament_length"], self.sports, eval_score)

        for sport in result:
            for event in result[sport]:
                complete_games.add_event(result[sport][event])
        return complete_games

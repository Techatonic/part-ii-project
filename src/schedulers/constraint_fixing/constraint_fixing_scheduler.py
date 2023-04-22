import copy
import math
from abc import ABC
import random
from typing import Type

from src.constraints.constraint import get_constraint_from_string, Constraint
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.games.complete_games import CompleteGames
from src.helper.helper import remove_duplicates_from_list
from src.rounds.knockout_rounds import generate_round_order, Round
from src.schedulers.scheduler import Scheduler
from src.schedulers.solver import Solver
from src.sports.sport import Sport
from src.venues.venue import Venue


# random.seed(1)


class ConstraintFixingScheduler(Scheduler, ABC):
    def __init__(self, solver: type[Solver], sports: dict[str, Sport], data: dict, forward_check: bool, events,
                 num_changes: int):
        """
        Class to solve the CSP scheduling problem
        :param solver: Type[Solver]
        :param sports: List[Sport]
        :param data: dict
        :param forward_check: bool
        :return result: dict[str, Event] | None
        """
        super().__init__(solver, sports, data, forward_check)
        self.events = events
        self.sports_data = {}
        self.num_changes_allowed = num_changes

    def schedule_events(self) -> CompleteGames | None:
        total_events = {}

        for sport in self.sports:
            sport = self.sports[sport]
            sport.constraints['required']["valid_match_time"] = {}
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
                "num_results_to_collect": 1,
                "comparator": None,
                "sport_specific": True,
                "sports": [sport],
                "wait_time": 5,
                "num_total_events": len(self.events),
                "assignments": self.events,
                "num_changes_allowed": self.num_changes_allowed
            })
            self.sports_data[sport.name] = csp_data

            csp_problem = self.__generate_constraint_checker_csp_problem(sport.name)

            result = csp_problem.solve()
            if result is None:
                return None

            # Add all sport-specific events to list of all events
            total_events[sport.name] = result

        complete_games = CompleteGames(self.data["tournament_length"], self.sports)
        for sport in total_events:
            for event in total_events[sport]:
                complete_games.add_event(total_events[sport][event])
        return complete_games

    def __generate_constraint_checker_csp_problem(self, sport_name: str):
        csp_problem = self.solver(self.sports_data[sport_name], forward_check=self.forward_check)
        sport = self.sports[sport_name]
        csp_problem.data["num_total_events"] = self.sports_data[sport_name]["num_total_events"]

        conflicts = self.data['conflicts']
        events_to_change = []
        for conflict in conflicts:
            events_to_change += conflict[1]

        events_to_change = remove_duplicates_from_list(events_to_change)
        events_to_change = [self.events[sport_name][event_name] for event_name in events_to_change if
                            event_name in self.events[sport_name]]

        for event_to_change in events_to_change:
            event_name = event_to_change.event_id

            options = []
            # Shuffle venues, days and times
            if "team_time_between_matches" in sport.constraints["required"]:
                specific_min_start_day = self.sports_data[sport_name]["min_start_day"] + \
                                         sport.constraints["required"]["team_time_between_matches"][
                                             "min_time_between_matches"] * (self.sports_data[sport_name]["round_order"][
                                                                                0].round_index - event_to_change.round.round_index)
                specific_max_finish_day = self.sports_data[sport_name]["max_finish_day"] - \
                                          sport.constraints["required"]["team_time_between_matches"][
                                              "min_time_between_matches"] * event_to_change.round.round_index
            else:
                specific_min_start_day = self.sports_data[sport_name]["min_start_day"] + \
                                         self.sports_data[sport_name]["round_order"][
                                             0].round_index - event_to_change.round.round_index
                specific_max_finish_day = self.sports_data[sport_name][
                                              "max_finish_day"] - event_to_change.round.round_index
            if specific_min_start_day >= specific_max_finish_day and len(
                    self.sports_data[sport_name]["round_order"]) > 1:
                handle_error("Insufficient number of days given for sport: ", sport.name)
            day_order = list(range(specific_min_start_day, specific_max_finish_day + 1))
            for venue in self.sports_data[sport_name]["venues"]:
                min_start_time = max(sport.min_start_time, venue.min_start_time)
                max_finish_time = min(sport.max_finish_time, venue.max_finish_time)
                time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration)))
                for time in time_order:
                    for day in day_order:
                        options.append(
                            Event(sport, event_to_change.event_id, venue=venue, event_round=event_to_change.round,
                                  day=day, start_time=time, duration=sport.match_duration,
                                  teams_involved=event_to_change.teams_involved))

            random.shuffle(options)

            csp_problem.add_variable(event_to_change.event_id, options)

        for sport_specific_constraint in sport.constraints["required"]:
            constraint: Type[Constraint] = get_constraint_from_string(sport_specific_constraint)
            # TODO This has been changed to make it so you just add the constraint, not the specific events involved.
            # TODO Fix the effects of this in other places, particularly with the constraint checker functionality
            csp_problem.add_constraint(constraint.constraint_string, sport=sport,
                                       params=sport.constraints["required"][sport_specific_constraint])

        return csp_problem

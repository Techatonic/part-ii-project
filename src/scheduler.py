import math
import random
from copy import deepcopy

from src.constraints.constraint import get_constraint_from_string, ConstraintType
from src.solvers.customised_solver import CustomisedSolver
from src.events.event import Event
from src.rounds.knockout_rounds import generate_round_order
from src.solvers.solver import Solver


def solve(solver, sports, tournament_length, general_constraints):
    """
    Method to solve the CSP scheduling problem
    :param solver
    :param sports: List[Sport]
    :param tournament_length: int
    :param general_constraints: List[string]
    :return result: List[Event] | None
    """

    total_events = []

    for sport in sports:
        csp_problem = solver()

        sport_name = sport.name
        venues = sport.possible_venues
        min_start_day = 0 if sport.min_start_day is None else sport.min_start_day
        max_finish_day = tournament_length if sport.max_finish_day is None else sport.max_finish_day

        # Define the variables
        # Add matches
        round_order = generate_round_order(sport.num_teams, sport.num_teams_per_game)
        variable_list = []

        match_num = 1
        for event_round in round_order:
            for _ in range(event_round.num_matches):
                options = []
                # Shuffle venues, days and times
                random.shuffle(venues)
                day_order = list(range(min_start_day, max_finish_day + 1))
                random.shuffle(day_order)

                for venue in venues:
                    min_start_time = max(sport.min_start_time, venue.min_start_time)
                    max_finish_time = min(sport.max_finish_time, venue.max_finish_time)
                    time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration)))
                    random.shuffle(time_order)
                    for day in day_order:
                        for time in time_order:
                            options.append(Event(sport, match_num, venue=venue, event_round=event_round,
                                                 day=day, start_time=time, duration=sport.match_duration))

                csp_problem.add_variable(sport_name + "_" + str(match_num), options)
                variable_list.append(sport_name + "_" + str(match_num))
                match_num += 1

        for sport_specific_constraint in sport.constraints:
            constraint = get_constraint_from_string(sport_specific_constraint)
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

        result = csp_problem.solve()
        # print("Done: " + sport.name)
        if result is None:
            return None
        # Add all sport-specific events to list of all events
        total_events.append(result)

    # print("Done individual sports. Beginning all sports")

    # Run CSP across all events in all sports
    total_csp_problem = CustomisedSolver()
    variable_list = []
    # print("Add variables")
    for sport in total_events:
        for event_name in sport:
            options = []
            min_start_time = max(sport[event_name].sport.min_start_time, sport[event_name].venue.min_start_time)
            max_finish_time = min(sport[event_name].sport.max_finish_time, sport[event_name].venue.max_finish_time)
            for time in range(min_start_time,
                              max_finish_time - math.ceil(sport[event_name].sport.match_duration) + 1):
                event_temp = deepcopy(sport[event_name])
                event_temp.start_time = time
                options.append(event_temp)
            total_csp_problem.add_variable(event_name, options)
            variable_list.append(event_name)

    # Add total sport constraints
    for general_constraint in general_constraints:
        constraint = get_constraint_from_string(general_constraint)
        if constraint.constraint_type == ConstraintType.UNARY:
            for event in variable_list:
                total_csp_problem.add_constraint(constraint.string_name, [event])
        elif constraint.constraint_type == ConstraintType.BINARY:
            for event_1 in range(len(variable_list)):
                for event_2 in range(event_1 + 1, len(variable_list)):
                    total_csp_problem.add_constraint(constraint.string_name,
                                                     [variable_list[event_1], variable_list[event_2]])
        else:
            total_csp_problem.add_constraint(constraint.string_name)

    result = total_csp_problem.solve()
    return result

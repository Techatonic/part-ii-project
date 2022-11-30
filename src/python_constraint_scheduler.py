import math
import random
from copy import deepcopy

from constraint import Problem

from .constraints.constraint import same_venue_overlapping_time, no_later_rounds_before_earlier_rounds, \
    same_venue_max_matches_per_day, get_constraint, ConstraintType
from .events.event import Event
from .rounds.knockout_rounds import generate_round_order


def solve(sports, tournament_length, general_constraints):
    """
        Method to solve the CSP scheduling problem
    """

    total_events = []

    for sport in sports:
        csp_problem = Problem()

        sport_name = sport.name
        venues = sport.possible_venues
        min_start_day = sport.min_start_day
        max_finish_day = tournament_length if sport.max_finish_day is None else sport.max_finish_day
        min_start_time = sport.min_start_time
        max_finish_time = sport.max_finish_time

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
                    min_start_time = max(min_start_time, venue.min_start_time)
                    max_finish_time = min(max_finish_time, venue.max_finish_time)
                    time_order = list(range(min_start_time, math.ceil(max_finish_time - sport.match_duration)))
                    if venue.name == "Stamford Bridge" and event_round.round_index == 0:
                        print(time_order)
                    random.shuffle(time_order)
                    for day in day_order:
                        for time in time_order:
                            options.append(Event(sport, match_num, venue=venue, event_round=event_round,
                                                 day=day, start_time=time, duration=sport.match_duration))

                csp_problem.addVariable(sport_name + "_" + str(match_num), options)
                variable_list.append(sport_name + "_" + str(match_num))
                match_num += 1

        for sport_specific_constraint in sport.constraints:
            constraint = get_constraint(sport_specific_constraint)
            if constraint.constraint_type == ConstraintType.UNARY:
                for event in variable_list:
                    csp_problem.addConstraint(constraint.function, [event])
            elif constraint.constraint_type == ConstraintType.BINARY:
                for event_1 in range(len(variable_list)):
                    for event_2 in range(event_1 + 1, len(variable_list)):
                        csp_problem.addConstraint(constraint.function,
                                                  [variable_list[event_1], variable_list[event_2]])
            else:
                csp_problem.addConstraint(constraint.function)

        result = csp_problem.getSolution()
        print("Done: " + sport.name)

        # Add all sport-specific events to list of all events
        total_events.append(result)

    print("Done individual sports. Beginning all sports")

    # Run CSP across all events in all sports
    total_csp_problem = Problem()
    variable_list = []
    for sport in total_events:
        for event_name in sport:
            options = []
            min_start_time = max(sport[event_name].sport.min_start_time, sport[event_name].venue.min_start_time)
            max_finish_time = min(sport[event_name].sport.max_finish_time, sport[event_name].venue.max_finish_time)
            for time in range(min_start_time, max_finish_time - math.ceil(sport[event_name].sport.match_duration) + 1):
                event_temp = deepcopy(sport[event_name])
                event_temp.start_time = time
                options.append(event_temp)
            total_csp_problem.addVariable(event_name, options)
            variable_list.append(event_name)

    # Add total sport constraints
    for general_constraint in general_constraints:
        constraint = get_constraint(general_constraint)
        if constraint.constraint_type == ConstraintType.UNARY:
            for event in variable_list:
                total_csp_problem.addConstraint(constraint.function, [event])
        elif constraint.constraint_type == ConstraintType.BINARY:
            for event_1 in range(len(variable_list)):
                for event_2 in range(event_1 + 1, len(variable_list)):
                    total_csp_problem.addConstraint(constraint.function,
                                                    [variable_list[event_1], variable_list[event_2]])
        else:
            total_csp_problem.addConstraint(constraint.function)

    result = total_csp_problem.getSolution()
    return result

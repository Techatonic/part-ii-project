import math
from copy import deepcopy

from constraint import Problem

from .constraints.constraint import same_venue_overlapping_time, no_later_rounds_before_earlier_rounds, \
    same_venue_max_matches_per_day
from .events.event import Event
from .rounds.knockout_rounds import generate_round_order


def solve(sports, tournament_length):
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
        # TODO add in multiple times
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
                for venue in venues:
                    for day in range(min_start_day, max_finish_day + 1):
                        for time in range(12, 14):
                            # for time in range(min_start_time, math.ceil(max_finish_time - sport.match_duration)):
                            # TODO Bring back multiple times in day
                            options.append(Event(sport, match_num, venue=venue, event_round=event_round,
                                                 day=day, start_time=time, duration=sport.match_duration))

                csp_problem.addVariable(sport_name + "_" + str(match_num), options)
                variable_list.append(sport_name + "_" + str(match_num))
                match_num += 1

        # Add binary constraints
        for match_1 in variable_list:
            for match_2 in variable_list:
                if match_1 != match_2:
                    matches_involved = [match_1, match_2]
                    # No overlapping matches in the same venue
                    csp_problem.addConstraint(same_venue_overlapping_time, matches_involved)
                    # No matches where a latter stage is taking place before an earlier stage
                    csp_problem.addConstraint(no_later_rounds_before_earlier_rounds, matches_involved)

        result = csp_problem.getSolution()

        # Add all sport-specific events to list of all events
        total_events.append(result)

    # TODO Run CSP across all events in all sports
    total_csp_problem = Problem()
    variable_list = []
    for sport in total_events:
        for event_name in sport:
            options = []
            event_temp = deepcopy(sport[event_name])
            min_start_time = max(event_temp.sport.min_start_time, event_temp.venue.min_start_time)
            max_finish_time = min(event_temp.sport.max_finish_time, event_temp.venue.max_finish_time)
            for time in range(min_start_time, max_finish_time):
                event_temp.start_time = time
                options.append(event_temp)
            total_csp_problem.addVariable(event_name, options)
            variable_list.append(event_name)

    # Add total sport constraints
    total_csp_problem.addConstraint(same_venue_max_matches_per_day)

    result = total_csp_problem.getSolution()
    return result

import math

from constraint import Problem, RecursiveBacktrackingSolver

from constraints.constraint import same_venue_overlapping_time, no_later_rounds_before_earlier_rounds
from events.event import Event
from rounds.knockout_rounds import QuarterFinal, SemiFinal, Final, RoundOf16


def solve(sports, days_of_tournament):
    """
        Method to solve the CSP scheduling problem
    """
    problem = Problem()

    # DELETE AFTER INTEGRATING MULTIPLE SPORTS
    sport = sports[0]
    venues = sport.possible_venues
    min_start_day = sport.min_start_day
    max_finish_day = days_of_tournament if sport.max_finish_day is None else sport.max_finish_day
    min_start_time = sport.min_start_time
    max_finish_time = sport.max_finish_time

    # Define the variables
    # Add football matches
    round_order = [
        RoundOf16(),
        QuarterFinal(),
        SemiFinal(),
        Final()
    ]
    total_number_of_matches = sum([round_type.num_matches for round_type in round_order])
    match_num = 1
    football_domain = []
    for event_round in round_order:
        for _ in range(event_round.num_matches):
            football_options = []
            for venue in venues:
                for day in range(min_start_day, max_finish_day + 1):
                    for time in range(min_start_time, math.ceil(max_finish_time - sport.match_duration)):
                        football_options.append(Event("football", match_num, venue=venue, event_round=event_round,
                                                      day=day, start_time=time, duration=sport.match_duration))

            problem.addVariable("football_" + str(match_num), football_options)
            football_domain += football_options
            match_num += 1

    # Add football constraints
    for football_match_1 in range(1, total_number_of_matches + 1):
        for football_match_2 in range(1, total_number_of_matches + 1):
            if football_match_1 != football_match_2:
                matches_involved = ["football_" + str(football_match_1), "football_" + str(football_match_2)]

                # No overlapping football matches in the same venue
                problem.addConstraint(same_venue_overlapping_time, matches_involved)

                # No football matches where a latter stage is taking place before an earlier stage
                problem.addConstraint(no_later_rounds_before_earlier_rounds, matches_involved)

    return problem.getSolution()

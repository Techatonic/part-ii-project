"""
    A script for generating a solution to a CST scheduling problem
"""
import constraint
from constraint import Problem

from events.event import Event
from rounds.knockout_rounds import QuarterFinal, SemiFinal, Final
from constraints.constraint import same_venue_overlapping_time, no_later_rounds_before_earlier_rounds

def solve():
    """
        Method to solve the CSP scheduling problem
    """
    problem = Problem()

    # Define the variables
    # Add football matches
    round_order = [
        QuarterFinal(),
        SemiFinal(),
        Final()
    ]
    total_number_of_matches = sum([round_type.num_matches for round_type in round_order])
    match_num = 1
    for event_round in round_order:
        for _ in range(event_round.num_matches):
            # TODO AUTOMATE THIS
            football_options = [
                Event('football', match_num, venue='Wembley', event_round=event_round, start_time=0,
                      duration=1),
                Event('football', match_num, venue='Wembley', event_round=event_round, start_time=6,
                      duration=1),
                Event('football', match_num, venue='Wembley', event_round=event_round, start_time=9,
                      duration=1),
                Event('football', match_num, venue='Olympic Stadium', event_round=event_round,
                      start_time=1,
                      duration=1),
                Event('football', match_num, venue='Olympic Stadium', event_round=event_round,
                      start_time=5,
                      duration=1),
                Event('football', match_num, venue='Olympic Stadium', event_round=event_round,
                      start_time=2,
                      duration=1),
                Event('football', match_num, venue='Stamford Bridge', event_round=event_round,
                      start_time=1,
                      duration=1),
                Event('football', match_num, venue='Stamford Bridge', event_round=event_round,
                      start_time=7,
                      duration=1),
            ]
            problem.addVariable("football_" + str(match_num), football_options)
            match_num += 1

    # Add football constraints
    for football_match_1 in range(1, total_number_of_matches + 1):
        for football_match_2 in range(1, total_number_of_matches + 1):
            if football_match_1 != football_match_2:
                # No overlapping football matches in the same venue
                problem.addConstraint(
                    same_venue_overlapping_time,
                    ["football_" + str(football_match_1), "football_" + str(football_match_2)]
                )

                # No football matches where a latter stage is taking place before an earlier stage
                problem.addConstraint(
                    no_later_rounds_before_earlier_rounds,
                    ["football_" + str(football_match_1), "football_" + str(football_match_2)]
                )

    return problem.getSolution()


result = solve()
for key in result:
    print(result[key])

"""
    A script for generating a solution to a CST scheduling problem
"""
from constraint import Problem


class Event:
    """
        Class for an event including its venue and start and end times
    """

    def __init__(
            self, sport, event_num, event_round=None, venue=None, start_time=None, duration=None
    ) -> None:
        self.round = event_round
        self.sport = sport
        self.event_num = event_num
        self.venue = venue
        self.start_time = start_time
        self.duration = duration

    def __str__(self) -> str:
        return f"""{{
            sport: {self.sport},
            event_num: {self.event_num},
            round: {self.round.round_name},
            venue: {self.venue},
            start_time: {self.start_time},
            duration: {self.duration}\n}}"""


class Round:
    """
        Class for defining the rounds of an event - e.g. semi-final
    """

    def __init__(self, round_name, num_matches=None, round_index=None) -> None:
        self.round_name = round_name
        if round_name == "quarter-final":
            self.num_matches = 4
            self.round_index = 2
        elif round_name == "semi-final":
            self.num_matches = 2
            self.round_index = 1
        elif round_name == "final":
            self.num_matches = 1
            self.round_index = 0
        else:
            self.num_matches = num_matches
            self.round_index = round_index


def solve():
    """
        Method to solve the CSP scheduling problem
    """
    problem = Problem()

    # Define the variables
    # Add football matches
    round_order = [
        Round('quarter-final'),
        Round('semi-final'),
        Round('final')
    ]
    total_number_of_matches = sum([round_type.num_matches for round_type in round_order])
    match_num = 1
    for event_round in round_order:
        for _ in range(event_round.num_matches):
            # TODO AUTOMATE THIS
            football_options = [
                Event('football', match_num, venue='Wembley', event_round=event_round, start_time=0, duration=1),
                Event('football', match_num, venue='Wembley', event_round=event_round, start_time=6, duration=1),
                Event('football', match_num, venue='Wembley', event_round=event_round, start_time=9, duration=1),
                Event('football', match_num, venue='Olympic Stadium', event_round=event_round, start_time=5,
                      duration=1),
                Event('football', match_num, venue='Olympic Stadium', event_round=event_round, start_time=1,
                      duration=1),
                Event('football', match_num, venue='Olympic Stadium', event_round=event_round, start_time=2,
                      duration=1),
                Event('football', match_num, venue='Stamford Bridge', event_round=event_round, start_time=1,
                      duration=1),
                Event('football', match_num, venue='Stamford Bridge', event_round=event_round, start_time=7,
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
                    lambda a, b:
                    not (a.venue == b.venue and (
                            (a.start_time <= b.start_time < a.start_time + a.duration) or
                            (b.start_time <= a.start_time < b.start_time + b.duration)
                    )),
                    ["football_" + str(football_match_1), "football_" + str(football_match_2)]
                )

                # No football matches where a latter stage is taking place before an earlier stage
                problem.addConstraint(
                    lambda a, b:
                    a.round.round_index == b.round.round_index or
                    a.round.round_index > b.round.round_index and a.start_time + a.duration <= b.start_time or
                    a.round.round_index < b.round.round_index and b.start_time + b.duration <= a.start_time,
                    ["football_" + str(football_match_1), "football_" + str(football_match_2)]
                )

    return problem.getSolution()


result = solve()
for key in result:
    print(result[key])

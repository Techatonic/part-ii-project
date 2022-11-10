class Round:
    """
        Defines a generic round of a tournament
    """

    def __init__(self, round_name, num_matches, round_index):
        self.round_name = round_name
        self.num_matches = num_matches
        self.round_index = round_index


knockout_rounds = [
    Round("Final", 1, 0),
    Round("Semi Final", 2, 1),
    Round("Quarter Final", 4, 2),
    Round("Round of 16", 8, 3),
    Round("Round of 32", 16, 4),
    Round("Round of 64", 32, 5),
    Round("Round of 128", 64, 6)
]


def generate_round_order(num_teams, num_teams_per_game):
    rounds = []
    teams = 2
    index = 0
    while teams <= num_teams:
        rounds.append(knockout_rounds[index])
        teams *= num_teams_per_game
        index += 1
    return rounds

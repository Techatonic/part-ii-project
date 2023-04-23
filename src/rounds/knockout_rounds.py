from src.error_handling.handle_error import handle_error


class Round:
    """
        Defines a generic round of a tournament
    """

    def __init__(self, round_name, num_matches, round_index):
        self.round_name = round_name
        self.num_matches = num_matches
        self.round_index = round_index

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return self.round_name

    def __eq__(self, other):
        return type(self) == type(other) and self.round_name == other.round_name


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


def convert_string_to_round_instance(round_string):
    for round_instance in knockout_rounds:
        if round_string == round_instance.round_name:
            return round_instance

    handle_error("No round of this name found: " + round_string)

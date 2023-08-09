from src.helper.handle_error import handle_error
from src.rounds.rounds import Round


class KnockoutRound(Round):
    """
    Defines a generic round of a tournament
    """

    def __init__(self, round_name, num_matches, round_index):
        self.round_name = round_name
        self.num_matches = num_matches
        self.round_index = round_index
        super().__init__(round_name, True, self, num_matches)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return self.round_name

    def __hash__(self):
        return hash((self.round_name, self.round_index, self.num_matches))

    def __eq__(self, other):
        return type(self) == type(other) and self.round_name == other.round_name


knockout_rounds = [
    KnockoutRound("Final", 1, 0),
    KnockoutRound("Semi Final", 2, 1),
    KnockoutRound("Quarter Final", 4, 2),
    KnockoutRound("Round of 16", 8, 3),
    KnockoutRound("Round of 32", 16, 4),
    KnockoutRound("Round of 64", 32, 5),
    KnockoutRound("Round of 128", 64, 6),
]


def generate_knockout_round_order(num_teams, num_teams_per_game, group_stage):
    if group_stage is not None:
        num_teams = group_stage.num_groups * group_stage.num_qualify_per_group
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

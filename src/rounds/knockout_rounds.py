class Round:
    """
        Defines a generic round of a tournament
    """
    def __init__(self, round_name, num_matches, round_index):
        self.round_name = round_name
        self.num_matches = num_matches
        self.round_index = round_index


class Final(Round):
    """
        Defines a final of a tournament
    """
    def __init__(self) -> None:
        super().__init__("Final", 1, 0)


class SemiFinal(Round):
    """
        Defines a semi-final of a tournament
    """
    def __init__(self) -> None:
        super().__init__("Semi Final", 2, 1)


class QuarterFinal(Round):
    """
        Defines a quarter-final of a tournament
    """
    def __init__(self) -> None:
        super().__init__("Quarter Final", 4, 2)

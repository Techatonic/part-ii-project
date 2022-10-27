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


class RoundOf16(Round):
    """
        Defines the round of 16 of a tournament
    """

    def __init__(self) -> None:
        super().__init__("Round of 16", 8, 3)


class RoundOf32(Round):
    """
        Defines the round of 32 of a tournament
    """

    def __init__(self) -> None:
        super().__init__("Round of 32", 16, 4)

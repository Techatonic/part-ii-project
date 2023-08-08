"""Import Modules"""
from src.venues.venue import Venue


class Sport:
    """
    Class defining a generic sport
    """

    def __init__(
        self,
        name,
        possible_venues: list[Venue],
        teams: list[str],
        num_teams_per_game: int,
        match_duration: float,
        is_knockout=True,
        min_start_day=1,
        max_finish_day=None,
        min_start_time=10,
        max_finish_time=22,
        constraints=None,
    ) -> None:
        self.name = name
        self.possible_venues = possible_venues
        self.teams = teams
        self.num_teams = len(teams)
        self.num_teams_per_game = num_teams_per_game
        self.match_duration = match_duration
        self.is_knockout = is_knockout
        self.min_start_day = min_start_day
        self.max_finish_day = max_finish_day
        self.min_start_time = min_start_time
        self.max_finish_time = max_finish_time
        self.constraints = constraints

    def __str__(self):
        return self.__repr__()

    def __hash__(self):
        return hash(self.name)

    def __repr__(self) -> str:
        return f"""{{
            sport: {self.name},
            venues: {self.possible_venues},
            teams: {self.teams},
            teams per game: {self.num_teams_per_game},
            match duration: {self.match_duration},
            is knockout?: {self.is_knockout},
            days of play: [{self.min_start_day}...{self.max_finish_day}],
            times of play: [{self.min_start_time}...{self.max_finish_time}],
            constraints: {self.constraints}
            \n}}"""

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.name == other.name

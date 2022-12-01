class Sport:
    """
        Class defining a generic sport
    """

    def __init__(self, name, possible_venues, num_teams, num_teams_per_game, match_duration, is_knockout=True,
                 group_stage=None, min_start_day=1, max_finish_day=None, min_start_time=10, max_finish_time=22,
                 constraints=None):
        self.name = name
        self.possible_venues = possible_venues
        self.num_teams = num_teams
        self.num_teams_per_game = num_teams_per_game
        self.match_duration = match_duration
        self.is_knockout = is_knockout
        self.min_start_day = min_start_day
        self.max_finish_day = max_finish_day
        self.min_start_time = min_start_time
        self.max_finish_time = max_finish_time
        self.group_stage = group_stage
        self.constraints = constraints

    def __str__(self):
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            sport: {self.name},
            venues: {self.possible_venues},
            number of teams: {self.num_teams},
            teams per game: {self.num_teams_per_game},
            match duration: {self.match_duration},
            is knockout?: {self.is_knockout},
            group stage?: {self.group_stage},
            days of play: [{self.min_start_day}...{self.max_finish_day}],
            times of play: [{self.min_start_time}...{self.max_finish_time}],
            constraints: {self.constraints}
            \n}}"""

    def __eq__(self, other):
        return self.name == other.name


def convert_string_to_sport_instance(sport_string, sports):
    for sport in sports:
        if sport_string == sport.name:
            return sport

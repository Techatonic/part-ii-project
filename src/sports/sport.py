class Sport:
    """
        Class defining a generic sport
    """

    def __init__(self, name, possible_venues, num_teams, is_knockout=True, has_group_stage=False, group_size=None,
                 min_start_day=1, max_start_day=None):
        self.name = name
        self.possible_venues = possible_venues
        self.num_teams = num_teams
        self.is_knockout = is_knockout
        self.has_group_stage = has_group_stage
        self.group_size = group_size
        self.min_start_day = min_start_day
        self.max_start_day = max_start_day

    def __str__(self) -> str:
        return f"""{{
            sport: {self.name},
            venues: {self.possible_venues},
            number of teams: {self.num_teams},
            is knockout?: {self.is_knockout},
            has group stage?: {self.has_group_stage},
            group size: {self.group_size}\n}}"""

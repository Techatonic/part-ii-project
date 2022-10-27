from sport import Sport


class Football(Sport):
    """
        Define football sport
    """
    def __init__(self, num_teams, venues, has_group_stage, group_size=None):
        super().__init__("Football", venues, num_teams, True, has_group_stage, group_size)

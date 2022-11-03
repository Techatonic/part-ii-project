from .sport import Sport


class Football(Sport):
    """
        Define football sport
    """
    def __init__(self, num_teams, venues, group_stage, min_start_day=1, max_finish_day=None, min_start_time=None,
                 max_finish_time=None):
        super().__init__("Football", venues, num_teams, 2, 1.5, True, group_stage, min_start_day, max_finish_day,
                         min_start_time, max_finish_time)

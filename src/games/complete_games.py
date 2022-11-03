class CompleteGames:
    events = []

    def __init__(self, days_of_tournament, sports):
        self.days_of_tournament = days_of_tournament
        self.sports = sports

    def set_event_times(self, events):
        self.events = events

    def __str__(self) -> str:
        return f"""{{
            days_of_tournament: {self.days_of_tournament},
            sports: {self.sports},
            events: {self.events}
        \n}}"""

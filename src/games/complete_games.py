class CompleteGames:
    events = []

    def __init__(self, days_of_tournament, sports):
        self.days_of_tournament = days_of_tournament
        self.sports = sports

    def add_event(self, event):
        # print(event)
        self.events.append(event)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            days_of_tournament: {self.days_of_tournament},
            sports: {self.sports},
            events: {self.events}
        \n}}"""

class Event:
    """
        Class for an event including its venue and start and end times
    """

    def __init__(
            self, sport, event_num, venue, event_round, day, start_time, duration, teams_involved=None) -> None:
        self.round = event_round
        self.sport = sport
        self.event_num = event_num
        self.venue = venue
        self.day = day
        self.start_time = start_time
        self.duration = duration
        # TODO Add teams involved to schema, example inputs and scheduler
        self.teams_involved = teams_involved

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            event_id: {str(self.event_num)},
            sport: {self.sport},
            round: {self.round},
            venue: {self.venue},
            day: {self.day},
            start_time: {self.start_time},
            duration: {self.duration},
            teams_involved: {self.teams_involved}
        \n}}"""

class Event:
    """
        Class for an event including its venue and start and end times
    """

    def __init__(
            self, sport, event_id, venue, event_round, day, start_time, duration, teams_involved=None) -> None:
        self.round = event_round
        self.sport = sport
        self.event_id = event_id
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
            event_id: {str(self.event_id)},
            sport: {self.sport},
            round: {self.round},
            venue: {self.venue},
            day: {self.day},
            start_time: {self.start_time},
            duration: {self.duration},
            teams_involved: {self.teams_involved}
        \n}}"""

    # Uses hash instead of __eq__ because Event classes are turned into Variable classes by the python-constraint module
    def __hash__(self):
        hash((self.round, self.sport, self.event_id, self.venue, self.day, self.start_time, self.duration,
              self.teams_involved))

    def __copy__(self):
        return Event(self.sport, self.event_id, self.venue, self.round, self.day, self.start_time, self.duration,
                     self.teams_involved)
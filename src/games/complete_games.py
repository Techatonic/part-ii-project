import json


class CompleteGames:
    complete_games = {}

    def __init__(self, days_of_tournament, sports, eval_score=None):
        self.complete_games["days_of_tournament"] = days_of_tournament
        self.complete_games["sports"] = sports
        self.complete_games["events"] = {}
        self.complete_games["eval_score"] = eval_score

    def add_event(self, event):
        if event.sport.name in self.complete_games["events"]:
            self.complete_games["events"][event.sport.name][event.id] = event
        else:
            self.complete_games["events"][event.sport.name] = {event.id: event}

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return json.dumps(
            self.complete_games, indent=4, default=lambda o: o.__dict__, skipkeys=True
        )

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.complete_games["days_of_tournament"]
            == other.complete_games["days_of_tournament"]
            and self.complete_games["sports"] == other.complete_games["sports"]
            and self.complete_games["events"] == other.complete_games["events"]
        )

    def export(self, path) -> None:
        for sport in self.complete_games["events"]:
            for event_id in self.complete_games["events"][sport]:
                event = self.complete_games["events"][sport][event_id]
                event.round = event.round.round_name
                event.sport = event.sport.name
                event.venue = event.venue.name

        dict_to_export = {
            "eval_score": self.complete_games["eval_score"],
            "events": self.complete_games["events"],
        }
        with open(path, "w") as file:
            json.dump(
                dict_to_export,
                file,
                indent=4,
                default=lambda o: o.__dict__,
                skipkeys=True,
            )

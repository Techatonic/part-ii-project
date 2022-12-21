import json


class CompleteGames:
    complete_games = {}

    def __init__(self, days_of_tournament, sports):
        self.complete_games["days_of_tournament"] = days_of_tournament
        self.complete_games["sports"] = sports
        self.complete_games["events"] = []

    def add_event(self, event):
        self.complete_games["events"].append(event)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return json.dumps(self.complete_games, indent=4, default=lambda o: o.__dict__, skipkeys=True)

    def __eq__(self, other):
        return self.complete_games["days_of_tournament"] == other.complete_games["days_of_tournament"] and \
            self.complete_games["sports"] == other.complete_games["sports"] and \
            self.complete_games["events"] == other.complete_games["events"]

    def export(self, path) -> None:
        for event in self.complete_games["events"]:
            event.round = event.round.round_name
            event.sport = event.sport.name
            event.venue = event.venue.name

        dict_to_export = {
            "events": self.complete_games["events"]
        }

        with open(path, "w") as file:
            json.dump(dict_to_export, file, indent=4, default=lambda o: o.__dict__, skipkeys=True)
        # print(json.dumps(dict_to_export, indent=4, default=lambda o: o.__dict__, skipkeys=True))
        print("Export successful to: " + path)

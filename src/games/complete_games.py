import json
import plotly.express as px
import pandas as pd


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

    def export(self, path, save_gantt_chart, start_date) -> None:
        if save_gantt_chart:
            self.__draw_gantt_chart(start_date)

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

    def __draw_gantt_chart(self, start_date):
        data_for_dict = []
        for sport_name, sport_events in self.complete_games["events"].items():
            for event_name, event in sport_events.items():
                data_for_dict.append(
                    {
                        "Event": event.id,
                        "Day": event.day,
                        "Start Hour": event.start_time,
                        "Duration": event.duration,
                        "Venue": event.venue.name,
                    }
                )

        df = pd.DataFrame(data_for_dict)

        df["Start_Datetime"] = (
            start_date
            + pd.to_timedelta(df["Day"] - 1, unit="D")
            + pd.to_timedelta(df["Start Hour"], unit="hour")
        )
        df["Finish_Datetime"] = df["Start_Datetime"] + pd.to_timedelta(
            df["Duration"], unit="hour"
        )

        venues = df["Venue"].unique()

        for venue in venues:
            venue_df = df[df["Venue"] == venue]

            fig = px.timeline(
                venue_df,
                x_start="Start_Datetime",
                x_end="Finish_Datetime",
                y="Event",
                facet_col="Venue",
                facet_col_wrap=1,
                facet_row_spacing=0.02,
            )

            fig.update_yaxes(
                autorange="reversed"
            )  # otherwise tasks are listed from the bottom up
            fig.write_html("././schedule_imgs/" + venue + ".html")
            fig.show()

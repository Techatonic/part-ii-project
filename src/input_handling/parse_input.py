from dateutil.parser import parse

from src.helper.handle_error import handle_error
from ..events.event import Event
from ..rounds.group_stage import GroupStage
from ..rounds.knockout_rounds import convert_string_to_round_instance
from ..sports.sport import Sport
from ..venues.venue import Venue, convert_string_to_venue_instance


def parse_input(json_input):
    try:
        data = json_input["data"]
        general_constraints = json_input["general_constraints"]
        sports = {}
        for sport in json_input["sports"].values():
            venues = []
            for venue in sport["venues"]:
                venues.append(parse_venue(venue))

            group_stage = None
            if sport["group_stage"] is not None:
                group_stage = parse_group_stage(
                    sport, sport["teams"], sport["group_stage"]
                )

            sports[sport["name"]] = Sport(
                sport["name"],
                venues,
                sport["teams"],
                sport["num_teams_per_game"],
                sport["duration"],
                sport["is_knockout"],
                sport["min_start_day"],
                sport["max_finish_day"],
                sport["min_start_time"],
                sport["max_finish_time"],
                sport["constraints"],
                group_stage,
            )

        try:
            print(data)
            data["start_date"] = parse(data["start_date"], dayfirst=True)
        except:
            handle_error("Start date is not formatted correctly in JSON input")

        return [sports, general_constraints, data]
    except Exception as e:
        print(e)
        handle_error("Parsing failed")


def parse_input_constraint_checker(json_input):
    try:
        [sports, general_constraints, data] = parse_input(json_input)
        venues = [venue for x in sports.values() for venue in x.possible_venues]
        events = {}

        for sport in json_input["sports"]:
            events[sport] = {}
            for event in json_input["sports"][sport]["events"]:
                events[sport][event["event_id"]] = Event(
                    sports[event["sport"]],
                    event["event_id"],
                    convert_string_to_venue_instance(event["venue"], venues),
                    convert_string_to_round_instance(event["round"]),
                    event["day"],
                    event["start_time"],
                    event["duration"],
                    event["teams_involved"],
                )
        return [sports, events, general_constraints, data]
    except Exception as e:
        print(e)
        handle_error("Parsing failed")


def parse_venue(venue):
    return Venue(
        venue["name"],
        venue["location_coordinates"],
        venue["location_address"],
        venue["location_postcode"],
        venue["capacity"],
        venue["min_start_time"],
        venue["max_finish_time"],
        venue["max_matches_per_day"],
    )


def parse_group_stage(sport, teams, group_stage):
    return GroupStage(
        sport, teams, group_stage["num_groups"], group_stage["num_qualify_per_group"]
    )

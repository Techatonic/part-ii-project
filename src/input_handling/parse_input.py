from ..error_handling.handle_error import handle_error
from ..events.event import Event
from ..rounds.knockout_rounds import convert_string_to_round_instance
from ..sports.sport import Sport, convert_string_to_sport_instance
from ..venues.venue import Venue, convert_string_to_venue_instance


def parse_input(json_input):
    try:
        data = json_input['data']
        general_constraints = json_input['general_constraints']
        sports = []

        for sport in json_input['sports']:
            venues = []
            for venue in sport['venues']:
                venues.append(parse_venue(venue))

            group_stage = None
            if group_stage is not None:
                group_stage = parse_group_stage(sport['group_stage'])

            sports.append(Sport(
                sport['name'],
                venues,
                sport['teams'],
                sport['num_teams_per_game'],
                sport['duration'],
                sport['is_knockout'],
                group_stage,
                sport['min_start_day'],
                sport['max_finish_day'],
                sport['min_start_time'],
                sport['max_finish_time'],
                sport['constraints']
            ))
        return [sports, general_constraints, data]
    except Exception as e:
        print(e)
        handle_error("Parsing failed")


def parse_input_constraint_checker(json_input):
    try:
        [sports, general_constraints, data] = parse_input(json_input)

        venues = [venue for x in sports for venue in x.possible_venues]

        events = []

        for event in json_input['events']:
            events.append(Event(
                convert_string_to_sport_instance(event["sport"], sports),
                event["event_id"],
                convert_string_to_venue_instance(event["venue"], venues),
                convert_string_to_round_instance(event["round"]),
                event["day"],
                event["start_time"],
                event["duration"],
                # TODO Add teams involved
            ))
        return [sports, events, general_constraints, data]
    except Exception as e:
        print(e)
        handle_error("Parsing failed")


def parse_venue(venue):
    return Venue(venue['name'], venue['location_coordinates'], venue['location_address'], venue['location_postcode'],
                 venue['capacity'], venue['min_start_time'], venue['max_finish_time'], venue['max_matches_per_day'])


def parse_group_stage(group_stage):
    # TODO Add parsing of group stage
    pass

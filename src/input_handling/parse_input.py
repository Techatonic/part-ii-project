from ..sports.sport import Sport
from ..venues.venue import Venue


def parse_input(json_input):
    days_of_tournament = json_input['tournament_length']
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
            sport['num_teams'],
            sport['num_teams_per_game'],
            sport['duration'],
            sport['is_knockout'],
            group_stage,
            sport['min_start_day'],
            sport['max_finish_day'],
            sport['min_start_time'],
            sport['max_finish_time']
        ))
    return [days_of_tournament, sports]


def parse_venue(venue):
    return Venue(venue['name'], venue['location_coordinates'], venue['location_address'], venue['location_postcode'],
                 venue['min_start_time'], venue['max_finish_time'], venue['capacity'])


def parse_group_stage(group_stage):
    # TODO Add parsing of group stage
    pass

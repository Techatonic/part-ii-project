from src.error_handling.handle_error import handle_error


class Venue:
    """
        Class defining a generic venue
    """

    def __init__(self, name, coordinates=None, address=None, postcode=None, capacity=None, min_start_time=1,
                 max_finish_time=24,
                 max_matches_per_day=1):
        self.name = name
        self.coordinates = coordinates
        self.address = address
        self.postcode = postcode
        self.min_start_time = min_start_time
        self.max_finish_time = max_finish_time
        self.capacity = capacity
        self.max_matches_per_day = max_matches_per_day

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            name: {self.name},
            coordinates: {self.coordinates},
            address: {self.address},
            postcode: {self.postcode},
            times of play: [{self.min_start_time}...{self.max_finish_time}]
            capacity: {self.capacity} 
            max matches per day: {self.max_matches_per_day}
            \n}}"""

    def __eq__(self, other):
        return self.name == other.name


def convert_string_to_venue_instance(venue_string, venues):
    for venue in venues:
        # print(venue_string)
        # print(venue)
        if venue_string == venue.name:
            return venue

    handle_error("No venue of this name found: " + venue_string)

class Venue:
    """
        Class defining a generic venue
    """

    def __init__(self, name, coordinates, address, postcode, capacity, min_start_time=1, max_finish_time=24,
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

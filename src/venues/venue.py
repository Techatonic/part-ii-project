class Venue:
    """
        Class defining a generic venue
    """

    def __init__(self, name, coordinates, address, postcode, min_start_time, max_finish_time, capacity):
        self.name = name
        self.coordinates = coordinates
        self.address = address
        self.postcode = postcode
        self.min_start_time = min_start_time
        self.max_finish_time = max_finish_time
        self.capacity = capacity

    def __str__(self) -> str:
        return f"""{{
            name: {self.name},
            coordinates: {self.coordinates},
            address: {self.address},
            postcode: {self.postcode},
            times of play: [{self.min_start_time}...{self.max_finish_time}]
            capacity: {self.capacity} 
            \n}}"""

class Round:
    def __init__(self, name, is_knockout, round_object, num_matches):
        self.round_name = name
        self.is_knockout = is_knockout
        self.round_object = round_object
        self.num_matches = num_matches
        self.round_index = float("inf")  # Set by default to infinity for group stage

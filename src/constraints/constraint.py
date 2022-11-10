def same_venue_overlapping_time(a, b):
    return not (a.venue == b.venue and a.day == b.day and (
            (a.start_time <= b.start_time < a.start_time + a.duration) or
            (b.start_time <= a.start_time < b.start_time + b.duration)
    ))


def no_later_rounds_before_earlier_rounds(a, b):
    return (a.round.round_index == b.round.round_index or
            a.round.round_index > b.round.round_index and a.day < b.day or
            a.round.round_index < b.round.round_index and b.day < a.day)


def same_venue_max_matches_per_day(*variables):
    venues = {}
    for event in variables:
        if not (event.venue.name in venues):
            venues[event.venue.name] = {event.day: 1}
        else:
            if not (event.day in venues[event.venue.name]):
                venues[event.venue.name][event.day] = 1
            else:
                venues[event.venue.name][event.day] += 1
            if venues[event.venue.name][event.day] > event.venue.max_matches_per_day:
                return False
    return True

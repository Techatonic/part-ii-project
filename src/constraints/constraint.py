def same_venue_overlapping_time(a, b):
    return not (a.venue == b.venue and (
            (a.start_time <= b.start_time < a.start_time + a.duration) or
            (b.start_time <= a.start_time < b.start_time + b.duration)
    ))


def no_later_rounds_before_earlier_rounds(a, b):
    return (a.round.round_index == b.round.round_index or
            a.round.round_index > b.round.round_index and a.start_time + a.duration <= b.start_time or
            a.round.round_index < b.round.round_index and
            b.start_time + b.duration <= a.start_time)

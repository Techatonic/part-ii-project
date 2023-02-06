import copy

from src.error_handling.handle_error import handle_error
from src.events.event import Event


def remove_tuple_from_events(input_val):
    if type(input_val) == tuple:
        if len(input_val) == 1:
            return input_val[0]
        return list(input_val)
    return input_val


def remove_scores_from_dict(input_dict: dict):
    new_dict = {}
    for sport in input_dict:
        new_dict[sport] = input_dict[sport][1]
    return new_dict


def flatten_events_by_sport_to_list(input_dict: dict[str, dict[str, Event]]) -> list[Event]:
    events = []
    for sport in input_dict:
        events += list(input_dict[sport].values())
    return events


def copy_assignments(assignments):
    try:
        new_assignments = {}
        for key in assignments:
            new_assignments[key] = assignments[key].__copy__()
        return new_assignments
    except:
        return copy.deepcopy(assignments)


def get_alL_events(events):
    result = {}
    for sport in events:
        result.update(events[sport])
    return result


def remove_duplicates_from_list(lst: list) -> list:
    new_list = []
    for item in lst:
        if not (item in new_list):
            new_list.append(item)
    return new_list

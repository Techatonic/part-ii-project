import copy

from src.events.event import Event
from src.helper import global_variables
from src.sports.sport import Sport


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
    # print("\n\n\n\n\n\n\n")
    # print(input_dict)
    events = []
    for sport in input_dict:
        events += list(input_dict[sport].values())
    return events


def flatten_events_by_sport_to_dict(input_dict: dict[str, dict[str, Event]]) -> dict[str, Event]:
    events = {}
    for sport in input_dict:
        for event in input_dict[sport]:
            events[event] = input_dict[sport][event]
    return events


def widen_events_to_events_by_sport(events: dict[str, Event]) -> dict[str, dict[str, Event]]:
    events_by_sport = {}
    for event in events:
        sport_name = events[event].sport.name
        if not (sport_name in events_by_sport):
            events_by_sport[sport_name] = {event: events[event]}
        else:
            events_by_sport[sport_name][event] = events[event]

    return events_by_sport


def convert_events_list_to_dict(events: list[Event]) -> dict[str, Event]:
    events_dict = {}
    for event in events:
        events_dict[event.event_id] = event
    return events_dict


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


def add_global_variables(sports: dict[str, Sport], data, general_constraints):
    global_variables.data = data
    for sport_name in sports:
        sport = sports[sport_name]
        global_variables.venues[sport_name] = sports[sport_name].possible_venues
        global_variables.constraint_params[sport_name]: dict[str, dict] = {
            "required": {},
            "optional": {}
        }
        for constraint in sport.constraints["required"]:
            global_variables.constraint_params[sport.name]["required"][constraint] = sport.constraints["required"][
                constraint]
        for constraint in sport.constraints["optional"]:
            global_variables.constraint_params[sport.name]["optional"][constraint] = sport.constraints["optional"][
                constraint]
    global_variables.constraint_params["general"] = general_constraints

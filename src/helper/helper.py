import copy

from src.error_handling.handle_error import handle_error
from src.events.event import Event


# def reformat_assignments(input_dict, type_wanted=list, keep_optimality_score=False):
#     if type(input_dict) == tuple:
#         if len(input_dict) == 1:
#             input_dict = input_dict[0]
#             # TODO Make this into new function. reformat should just be to remove the tuple. Different functions for
#             #   converting to list and dict
#             if type_wanted == list:
#                 return list(input_dict.values())
#             elif type_wanted == dict:
#                 if keep_optimality_score:
#                     return input_dict
#                 else:
#                     return {sport: input_dict[sport][1] for sport in input_dict}
#     handle_error("Unknown Error in constraint. Please try again")


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

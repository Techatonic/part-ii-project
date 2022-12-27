from src.error_handling.handle_error import handle_error
from src.events.event import Event


def convert_possible_tuple_to_list(lst):
    if type(lst) == tuple:
        if len(lst) == 1:
            lst = lst[0]
            if not type(lst) == list:
                if type(lst) == Event:
                    return [lst]
                else:
                    handle_error("Unknown Error in constraint. Please try again")
    return lst
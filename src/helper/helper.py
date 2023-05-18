import copy

from src.events.event import Event
from src.helper import global_variables
from src.helper.handle_error import handle_error
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


def flatten_events_by_sport_to_dict_with_scores(input_dict: tuple[float, dict[str, dict[str, Event]]]) -> dict[
        str, Event]:
    events = {}
    for sport in input_dict[1]:
        for event in input_dict[1][sport][1]:
            events[event] = input_dict[1][sport][1][event]
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
        events_dict[event.id] = event
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


def heuristic(assignments: dict[str, dict[str, Event]], optional_constraints, csp_instance) -> float:
    if len(optional_constraints) == 0:
        return 1
    normalising_factor = sum(
        optional_constraint_heuristic.get_params()["weight"] for optional_constraint_heuristic in
        optional_constraints)

    if normalising_factor == 0:
        handle_error("Weights of optional constraints sum to 0")
    assignments_by_sport_with_tuple = {}
    for sport in assignments:
        assignments_by_sport_with_tuple[sport] = (0, assignments[sport])

    score = 0
    for heuristic in optional_constraints:
        if heuristic.get_sport() is None:
            from src.constraints.optional_constraints import take_average_of_heuristics_across_all_sports
            score += take_average_of_heuristics_across_all_sports(csp_instance, assignments,
                                                                  heuristic) * heuristic.get_params()["weight"]
        else:
            if heuristic.get_sport().name in assignments:
                individual_score = heuristic.eval_constraint(csp_instance,
                                                             {heuristic.get_sport().name: assignments[
                                                                 heuristic.get_sport().name]})[
                    1] * heuristic.get_params()["weight"]
                if individual_score < 0 or individual_score > 1:
                    handle_error(
                        f'Constraint eval score out of bounds: \nsport: {heuristic.get_sport().name}  -  constraint: {heuristic.get_constraint_string()}  -  score: {individual_score}')
                score += individual_score
            else:
                normalising_factor -= 1
    return score / normalising_factor


def calculate_fitness(assignments: dict[str, dict[str, Event]], constraints,
                      optional_constraints, csp_instance, accept_invalid_solutions=False) -> float:
    from src.constraints.constraint_checker import constraint_check
    constraints_broken = 0
    assignments_flatten = flatten_events_by_sport_to_dict(assignments)
    for constraint in constraints:
        if constraint.get_sport() is None:
            constraints_broken += len(constraint_check(constraint,
                                      assignments_flatten)) > 0
        else:
            sport_name = constraint.get_sport().name
            constraints_broken += len(constraint_check(constraint,
                                      assignments[sport_name])) > 0

    optional_constraints_score = heuristic(
        assignments, optional_constraints, csp_instance)
    if constraints_broken > 0 and not accept_invalid_solutions:
        return 0
    return optional_constraints_score / (2 ** constraints_broken)

from typing import Type

from src.constraints.constraint import Constraint, ConstraintType
from src.constraints.constraint_checker import constraint_check, valid_constraint_check
from src.helper.priority_queue import PriorityQueue
from src.schedulers.solver import Solver


def ac3(queue: PriorityQueue, constraints: list[Constraint]) -> object:
    done = False

    temp_queue = queue.__copy__()
    unary_constraints = list(
        filter(lambda constraint: constraint.get_constraint_type() == ConstraintType.UNARY, constraints))
    binary_constraints = list(
        filter(lambda constraint: constraint.get_constraint_type() == ConstraintType.BINARY, constraints))
    all_constraints = list(
        filter(lambda constraint: constraint.get_constraint_type() == ConstraintType.ALL, constraints))

    for unary_constraint in unary_constraints:
        for variable in temp_queue.variables:
            variable.domain = [option for option in variable.domain if
                               valid_constraint_check(unary_constraint, {option.id: option})]

    worklist = [(x, y) for x in temp_queue.variables for y in temp_queue.variables if x != y]

    while len(worklist) > 0:
        (x, y) = worklist.pop(0)
        changes_made = arc_reduce(x, y, binary_constraints, all_constraints)
        if changes_made > 0:
            if not done:
                done = True
            if len(x.domain) == 0:
                return False, None

            worklist += [(x, z) for z in temp_queue.variables if z != y and z != x]

    return True, temp_queue


def arc_reduce(x, y, binary_constraints, all_constraints):
    changes_made = 0
    for x_option in x.domain:
        found_valid_pair = False
        for y_option in y.domain:
            if all(valid_constraint_check(binary_constraint, {x_option.id: x_option, y_option.id: y_option}) for
                   binary_constraint in binary_constraints):
                # Treat all_constraints as binary constraints for AC-3
                if all(valid_constraint_check(all_constraint, {x_option.id: x_option, y_option.id: y_option}) for
                       all_constraint in all_constraints):
                    found_valid_pair = True
                    break
        if not found_valid_pair:
            x.domain.remove(x_option)
            changes_made += 1
    return changes_made

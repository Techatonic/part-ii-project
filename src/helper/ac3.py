from src.constraints.constraint import Constraint, ConstraintType
from src.constraints.constraint_checker import constraint_check, valid_constraint_check
from src.helper.priority_queue import PriorityQueue
from src.schedulers.solvers.solver import Solver


def ac3(csp_instance: Solver, queue: PriorityQueue, constraints: list[Constraint]) -> object:
    temp_queue = queue.__copy__()
    unary_constraints = list(
        filter(lambda constraint: constraint.constraint_type == ConstraintType.UNARY, constraints))
    binary_constraints = list(
        filter(lambda constraint: constraint.constraint_type == ConstraintType.BINARY, constraints))
    for unary_constraint in unary_constraints:
        for variable in temp_queue.variables:
            variable.domain = [option for option in variable.domain if
                               constraint_check(csp_instance, unary_constraint.constraint, [option],
                                                unary_constraint.params)]

    worklist = [(x, y) for x in temp_queue.variables for y in temp_queue.variables if x != y]
    # Use for options 2+3
    # made_change = False
    # PERCENT_THRESHOLD = 0.1

    while len(worklist) > 0:
        (x, y) = worklist.pop(0)
        changes_made = arc_reduce(x, y, binary_constraints)
        if changes_made > 0:
            if len(x.domain) == 0:
                print("AC-3 return false - ", x.variable)
                queue.set(temp_queue.variables)
                return False
            # Option 1: Add to worklist
            worklist += [(x, z) for z in temp_queue.variables if z != y and z != x]

            # Option 3: Rerun AC algorithm once finished if change has been made
            # made_change = True

            # Option 2: Rerun aC algorithm once finished if not many changes. If many changes, add to worklist
            # if changes_made < PERCENT_THRESHOLD * len(x.domain):
            #    made_change = True
            # else:
            #    worklist += [(x, z) for z in queue.variables if z != y and z != x]

    queue.set(temp_queue.variables)

    # Use this if statement for options 2+3
    # if made_change:
    #    return ac3(queue, constraints)

    return True


def arc_reduce(x, y, binary_constraints):
    changes_made = 0
    for x_option in x.domain:
        found_valid_pair = False
        for y_option in y.domain:
            # TODO Because the binary constraints are now all constraints, do this for 'ALL' constraints too (but can just pass in the two events)
            if all(valid_constraint_check(binary_constraint.constraint, [x_option, y_option], binary_constraint.params)
                   for binary_constraint in binary_constraints):
                found_valid_pair = True
                break
        if not found_valid_pair:
            x.domain.remove(x_option)
            changes_made += 1
    return changes_made

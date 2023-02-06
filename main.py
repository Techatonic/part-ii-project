"""
    A script for generating a solution to a CST scheduling problem
"""
# TODO Make all copies use custom deepcopy
import time
import os
from argparse import ArgumentParser

from src.constraints.constraint_checker import constraint_checker
from src.error_handling.handle_error import handle_error
from src.helper import global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input, parse_input_constraint_checker
from src.schedulers.solvers.constraint_fixing.constraint_fixing_scheduler import ConstraintFixingScheduler
from src.schedulers.solvers.constraint_fixing.constraint_fixing_solver import ConstraintFixingSolver
from src.schedulers.solvers.csop.csop_scheduler import CSOPScheduler
from src.schedulers.solvers.csop.csop_solver import CSOPSolver
from src.schedulers.solvers.csp.csp_scheduler import CSPScheduler
from src.schedulers.solvers.csp.csp_solver import CSPSolver
from src.schedulers.solvers.csp_module.module_solver import ModuleSolver
from src.sports.sport import Sport


def main(input_path: str, export_path: str | None = None, constraint_checker_flag: int = 1,
         use_python_module: bool = False, use_csop_solver: bool = False, forward_check=False) -> None:
    if constraint_checker_flag:
        run_constraint_checker(input_path, export_path, constraint_checker_flag)
    else:
        run_solver(input_path, use_python_module, use_csop_solver, forward_check, export_path)


def run_constraint_checker(input_path: str, export_path: str | None = None, num_changes=1) -> None:
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema_constraint_checker.json')

    [sports, events, general_constraints, data] = parse_input_constraint_checker(input_json)
    add_global_variables(sports, data, general_constraints)

    default_constraints = {"valid_match_time": {}}
    general_constraints['required'].update(default_constraints)

    conflicts = constraint_checker(sports, events, general_constraints)
    # print(conflicts)

    if len(conflicts) == 0:
        print("No conflicts found - all constraints are satisfied")
    else:
        handle_error("Errors found - See below:", exit_program=False)
        for conflict in conflicts:
            conflict_str = conflict[0].ljust(35) + str(conflict[1])
            handle_error(conflict_str, exit_program=False)
        data['conflicts'] = conflicts

        scheduler = ConstraintFixingScheduler(ConstraintFixingSolver, sports, data, False, events, num_changes)

        result = scheduler.schedule_events()
        if result is None:
            handle_error("No results found")

        if export_path is not None:
            try:
                result.export(export_path)

            except Exception as e:
                print(e)
                handle_error("Export failed. Please try again ensuring a valid output path is given")
        else:
            print("No export path given")

    exit()


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


def run_solver(input_path: str, use_python_module: bool, use_csop_solver: bool, forward_check: bool,
               export_path: str | None = None) -> None:
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema.json')

    [sports, general_constraints, data] = parse_input(input_json)
    add_global_variables(sports, data, general_constraints)
    data["general_constraints"] = general_constraints

    solver = None
    scheduler = None
    if use_python_module:
        solver = ModuleSolver
        scheduler = CSPScheduler
    else:
        if not use_csop_solver:
            solver = CSPSolver
            scheduler = CSPScheduler
        else:
            solver = CSOPSolver
            scheduler = CSOPScheduler

    scheduler = scheduler(solver, sports, data, forward_check)
    result = scheduler.schedule_events()

    if result is None:
        handle_error("No results found")

    if export_path is not None:
        try:
            result.export(export_path)

        except Exception as e:
            print(e)
            handle_error("Export failed. Please try again ensuring a valid output path is given")


if __name__ == "__main__":
    # Setup command line arguments
    parser = ArgumentParser('Automated Event Scheduler')
    parser.add_argument("--import_path", required=True, type=str, help="read json input from this path")
    parser.add_argument("--export_path", required=False, type=str, help="export json output to this path")
    parser.add_argument("-c", required=False, type=int,
                        help="run input_path on constraint checker and allow up to c changed events")
    parser.add_argument("-m", action='store_true', help="run on python-constraint CSP solver")
    parser.add_argument("-o", action='store_true',
                        help="run on CSOP solver, will take longer to run but produce more optimal results")
    parser.add_argument("-forward_check", action='store_true', help="run forward checking algorithm on solver")
    args = None
    try:
        args = parser.parse_args()
    except:
        handle_error("Invalid input. Please ensure you provide all required arguments")

    if not os.path.exists(args.import_path):
        handle_error("Path does not exist")
    if (args.c is not None) + args.m + args.o > 1:
        handle_error("Can select only one of constraint checker, python-constraint CSP solver and CSOP solver")

    start_time = time.time()

    if args.export_path:
        main(args.import_path, args.export_path, constraint_checker_flag=args.c, use_python_module=args.m,
             use_csop_solver=args.o, forward_check=args.forward_check)
    else:
        main(args.import_path, constraint_checker_flag=args.c)

    end_time = time.time()
    print("Time Taken: " + str(end_time - start_time))

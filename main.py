"""
    A script for generating a solution to a CST scheduling problem
"""
# TODO Make all copies use custom deepcopy
import time
import os
from argparse import ArgumentParser

from src.constraints.constraint_checker import constraint_checker
from src.error_handling.handle_error import handle_error
from src.games.complete_games import CompleteGames
from src.helper import global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input, parse_input_constraint_checker
from src.schedulers.solvers.csop_scheduler import CSOPScheduler
from src.schedulers.solvers.csop_solver import CSOPSolver
from src.schedulers.solvers.csp_scheduler import CSPScheduler
from src.schedulers.solvers.customised_solver import CustomisedSolver
from src.schedulers.solvers.module_solver import ModuleSolver
from src.schedulers.solvers.solver import SolverType
from src.sports.sport import Sport


def main(input_path: str, export_path: str | None = None, constraint_checker_flag: bool = False,
         use_python_module: bool = False, use_csop_solver: bool = False, forward_check=False) -> None:
    if constraint_checker_flag:
        run_constraint_checker(input_path)
    else:
        run_solver(input_path, use_python_module, use_csop_solver, forward_check, export_path)


def run_constraint_checker(input_path: str) -> None:
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema_constraint_checker.json')

    [sports, events, general_constraints, data] = parse_input_constraint_checker(input_json)
    add_global_variables(sports, data, general_constraints)

    default_constraints = {"valid_match_time": {}}
    general_constraints['required'].update(default_constraints)
    print(general_constraints)

    conflicts = constraint_checker(sports, events, general_constraints)

    if len(conflicts) == 0:
        print("No conflicts found - all constraints are satisfied")
    else:
        handle_error("Errors found - See below:", exit_program=False)
        for conflict in conflicts:
            handle_error(str(conflict), exit_program=False)
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

    complete_games = CompleteGames(data["tournament_length"], sports)

    solver = None
    solver_type = None
    scheduler_type = None
    if use_python_module:
        solver = ModuleSolver
        solver_type = SolverType.PYTHON_CONSTRAINT_SOLVER
        scheduler_type = CSPScheduler
    else:
        if not use_csop_solver:
            solver = CustomisedSolver
            solver_type = SolverType.CUSTOMISED_SOLVER
            scheduler_type = CSPScheduler
        else:
            solver = CSOPSolver
            solver_type = SolverType.CSOP_SOLVER
            scheduler_type = CSOPScheduler

    scheduler = scheduler_type(solver, solver_type, sports, data, forward_check)
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
    parser.add_argument("-c", action='store_true', help="run input_path on constraint checker")
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
    if args.c + args.m + args.o > 1:
        handle_error("Can select only one of constraint checker, python-constraint CSP solver and CSOP solver")

    start_time = time.time()

    if args.export_path:
        main(args.import_path, args.export_path, constraint_checker_flag=args.c, use_python_module=args.m,
             use_csop_solver=args.o, forward_check=args.forward_check)
    else:
        main(args.import_path, constraint_checker_flag=args.c)

    end_time = time.time()
    print("Time Taken: " + str(end_time - start_time))

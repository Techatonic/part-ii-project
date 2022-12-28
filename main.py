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
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input, parse_input_constraint_checker
from src.scheduler import solve
from src.solvers.customised_solver import CustomisedSolver
from src.solvers.module_solver import ModuleSolver


def main(input_path: str, export_path: str | None = None, constraint_checker_flag: bool = False,
         use_python_module: bool = False, forward_check=False) -> None:
    if constraint_checker_flag:
        run_constraint_checker(input_path)
    else:
        run_solver(input_path, use_python_module, forward_check, export_path)


def run_constraint_checker(input_path: str) -> None:
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema_constraint_checker.json')

    [_, sports, events, general_constraints] = parse_input_constraint_checker(input_json)

    conflicts = constraint_checker(sports, events, general_constraints)

    if len(conflicts) == 0:
        print("No conflicts found - all constraints are satisfied")
    else:
        handle_error("Errors found - See below:", exit_program=False)
        for conflict in conflicts:
            handle_error(str(conflict), exit_program=False)
    exit()


def run_solver(input_path: str, use_python_module: bool, forward_check: bool, export_path: str | None = None, ) -> None:
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema.json')

    [tournament_length, sports, general_constraints] = parse_input(input_json)

    complete_games = CompleteGames(tournament_length, sports)

    solver = None
    if use_python_module:
        solver = ModuleSolver
    else:
        solver = CustomisedSolver

    result = solve(solver, sports, tournament_length, general_constraints, forward_check)

    if result is None:
        handle_error("No results found")

    for event_key in result:
        complete_games.add_event(result[event_key])

    if export_path is not None:
        try:
            complete_games.export(export_path)
        except:
            handle_error("Export failed. Please try again ensuring a valid output path is given")


if __name__ == "__main__":
    # Setup command line arguments
    parser = ArgumentParser('Automated Event Scheduler')
    parser.add_argument("--import_path", required=True, type=str, help="read json input from this path")
    parser.add_argument("--export_path", required=False, type=str, help="export json output to this path")
    parser.add_argument("-c", action='store_true', help="run input_path on constraint checker")
    parser.add_argument("-m", action='store_true', help="run on python-constraint CSP solver")
    parser.add_argument("-forward_check", action='store_true', help="run forward checking algorithm on solver")
    args = None
    try:
        args = parser.parse_args()
    except:
        handle_error("Invalid input. Please ensure you provide all required arguments")

    if not os.path.exists(args.import_path):
        handle_error("Path does not exist")
    start_time = time.time()

    if args.export_path:
        main(args.import_path, args.export_path, constraint_checker_flag=args.c, use_python_module=args.m,
             forward_check=args.forward_check)
    else:
        main(args.import_path, constraint_checker_flag=args.c)

    end_time = time.time()
    print("Time Taken: " + str(end_time - start_time))

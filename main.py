"""
    A script for generating a solution to a CST scheduling problem
"""
import time
import os
from argparse import ArgumentParser

from src.constraints.constraint_checker import constraint_checker
from src.error_handling.handle_error import handle_error
from src.games.complete_games import CompleteGames
from src.python_constraint_scheduler import solve as python_module_constraint_solver
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input, parse_input_constraint_checker
from src.python_customised_scheduler import solve as python_customised_solver


def main(input_path, export_path=None, constraint_checker_flag=False, use_python_module=False):
    if constraint_checker_flag:
        run_constraint_checker(input_path)
    else:
        run_solver(input_path, use_python_module, export_path)


def run_constraint_checker(input_path):
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema_constraint_checker.json')

    [tournament_length, sports, events, general_constraints] = parse_input_constraint_checker(input_json)

    conflicts = constraint_checker(tournament_length, sports, events, general_constraints)

    if len(conflicts) == 0:
        print("No conflicts found - all constraints are satisfied")
    else:
        handle_error("Errors found - See below:", exit_program=False)
        for conflict in conflicts:
            handle_error(str(conflict), exit_program=False)
    exit()


def run_solver(input_path, use_python_module, export_path=None):
    input_json = read_and_validate_input(input_path, 'src/input_handling/input_schema.json')

    [tournament_length, sports, general_constraints] = parse_input(input_json)

    complete_games = CompleteGames(tournament_length, sports)

    result = None
    if use_python_module:
        result = python_module_constraint_solver(sports, tournament_length, general_constraints)
    else:
        result = python_customised_solver(sports, tournament_length, general_constraints)

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
    args = None
    try:
        args = parser.parse_args()
    except:
        handle_error("Invalid input. Please ensure you provide all required arguments")

    if not os.path.exists(args.import_path):
        handle_error("Path does not exist")
    start_time = time.time()

    if args.export_path:
        main(args.import_path, args.export_path, constraint_checker_flag=args.c, use_python_module=args.m)
    else:
        main(args.import_path, constraint_checker_flag=args.c)

    end_time = time.time()
    print("\nTime Taken: " + str(end_time - start_time))

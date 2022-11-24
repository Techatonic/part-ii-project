"""
    A script for generating a solution to a CST scheduling problem
"""
import time
import os
from argparse import ArgumentParser

from src.error_handling.handle_error import handle_error
from src.games.complete_games import CompleteGames
from src.python_constraint_scheduler import solve
from src.input_handling.input_reader import read_input
from src.input_handling.parse_input import parse_input


def main(json_path, export_path=None):
    input_json = read_input(json_path)

    [tournament_length, sports] = parse_input(input_json)

    complete_games = CompleteGames(tournament_length, sports)

    result = solve(sports, tournament_length)

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
    args = None
    try:
        args = parser.parse_args()
    except:
        handle_error("Invalid input. Please ensure you provide all required arguments")

    if not os.path.exists(args.import_path):
        handle_error("Path does not exist")
    start_time = time.time()

    if args.export_path:
        main(args.import_path, args.export_path)
    else:
        main(args.import_path)

    end_time = time.time()
    print("\nTime Taken: " + str(end_time - start_time))

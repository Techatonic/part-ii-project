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


def main(json_path):
    input_json = read_input(json_path)

    [tournament_length, sports] = parse_input(input_json)

    complete_games = CompleteGames(tournament_length, sports)

    result = solve(sports, tournament_length)
    for event in result:
        complete_games.add_event_time(event)

    print(complete_games)


if __name__ == "__main__":
    # Setup command line arguments
    parser = ArgumentParser('Automated Event Scheduler')
    parser.add_argument("path", type=str, help="read json input from this path")
    args = parser.parse_args()
    if not os.path.exists(args.path):
        handle_error("Path does not exist")
    start_time = time.time()
    main(args.path)
    end_time = time.time()
    print("\nTime Taken: " + str(end_time - start_time))

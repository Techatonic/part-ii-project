"""
    A script for generating a solution to a CST scheduling problem
"""
import time

from src.games.complete_games import CompleteGames
from src.python_constraint_scheduler import solve
from src.input_handling.input_reader import read_input
from src.input_handling.parse_input import parse_input


def main():
    input_json = read_input('examples/example_input.json')

    [tournament_length, sports] = parse_input(input_json)

    complete_games = CompleteGames(tournament_length, sports)

    result = solve(sports, tournament_length)
    print(result)
    for event in result:
        complete_games.add_event_time(event)

    print(complete_games)


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print("\nTime Taken: " + str(end_time - start_time))

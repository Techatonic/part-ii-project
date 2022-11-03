"""
    A script for generating a solution to a CST scheduling problem
"""
import time

from python_constraint_scheduler import solve
from sports.football import Football


def main():
    start_time = time.time()

    days_of_tournament = 14

    sports = [
        Football(16, ["Stamford Bridge", "Olympic Stadium", "Emirates Stadium", "Old Trafford"], None, min_start_day=1,
                 max_finish_day=8, min_start_time=15, max_finish_time=22)
    ]

    result = solve(sports, days_of_tournament)

    for key in result:
        print(result[key])

    end_time = time.time()
    print("\nTime Taken: " + str(end_time - start_time))


if __name__ == "__main__":
    main()

"""
    A script for generating a solution to a CST scheduling problem
"""

from python_constraint_scheduler import solve
from sports.sport import Sport


def main():
    sports = [
        Sport("Football", ["Stamford Bridge", "Olympic Stadium", "Emirates Stadium", "Old Trafford"], num_teams=16,
              min_start_day=1, max_start_day=6)
    ]
    days_of_tournament = 14

    result = solve(sports, days_of_tournament)

    for key in result:
        print(result[key])


if __name__ == "__main__":
    main()

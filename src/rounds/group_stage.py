import pprint

from src.helper.handle_error import handle_error
from src.rounds.rounds import Round


class GroupStage(Round):
    def __init__(self, sport, teams, num_groups, num_qualify_per_group):
        self.sport = sport
        self.teams = teams
        self.num_teams = len(self.teams)
        self.num_groups = num_groups
        if self.num_teams % self.num_groups != 0:
            handle_error("Number of groups must divide the number of teams")
        self.group_size = self.num_teams // self.num_groups
        self.groups = self.__generate_groups()
        self.num_qualify_per_group = num_qualify_per_group

        self.num_matches = self.num_groups * self.group_size * (self.group_size - 1) / 2

        super().__init__("Group Stage", False, self, self.num_matches)

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return (
            f"Group Stage: {self.num_teams} teams in {self.num_groups} groups with {self.num_qualify_per_group} "
            f"teams qualifying per group"
        )

    def __hash__(self) -> int:
        return hash(
            (self.sport, self.num_teams, self.num_groups, self.num_qualify_per_group)
        )

    def __eq__(self, other):
        return (
            type(self) == type(other)
            and self.sport == other.sport
            and self.num_teams == other.num_teams
            and self.num_groups == other.num_groups
            and self.num_qualify_per_group == other.num_qualify_per_group
        )

    def generate_group_stage_matches(self):
        matches = []
        # print(self.groups)
        for group_key, group in self.groups.items():
            for team_1 in range(len(group)):
                for team_2 in range(team_1 + 1, len(group)):
                    matches.append([group[team_1], group[team_2]])
        # print(f"Matches: {matches}")
        return matches

    def __generate_groups(self):
        groups = {}
        for group_num in range(self.num_groups):
            groups[group_num] = self.teams[
                self.group_size * group_num : self.group_size * (group_num + 1)
            ]
        return groups

    def generate_knockout_round_matches(self):
        teams_going_forward = []
        for group_key, group in self.groups.items():
            for i in range(self.num_qualify_per_group):
                teams_going_forward.append(["".join(group) + str(i + 1)])
        print(teams_going_forward)
        return teams_going_forward

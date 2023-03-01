import copy
import time
import random

from src.constraints.constraint import Constraint, get_constraint_from_string, ConstraintType
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_optional_constraint_from_string, \
    get_inequality_operator_from_input, take_average_of_heuristics_across_all_sports
from src.error_handling.handle_error import handle_error
from src.events.event import Event

from src.sports.sport import Sport


class GeneticAlgorithmSolver:
    def __init__(self, data=None, forward_check=False) -> None:
        self.data = data if data is not None else {}

        self.constraints: list[Constraint] = []
        self.optional_constraints: list[Constraint] = []
        self.forward_check: bool = forward_check
        self.variables = {}

    def add_variable(self, new_var: str, domain) -> None:
        if new_var in self.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.variables[new_var] = domain

    def get_variables(self) -> dict:
        return self.variables

    def add_constraint(self, function_name: str, variables: list[str] | None = None,
                       sport: Sport | None = None, params: dict = None) -> None:
        function = get_constraint_from_string(function_name)
        self.constraints.append(Constraint(function, variables, sport, copy.deepcopy(params)))

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params=None):
        params_copy = copy.deepcopy(params)
        if params_copy is None:
            params_copy = {}
        if not ("weight" in params_copy):
            params_copy["weight"] = 1
        if "inequality" in params_copy:
            params_copy["inequality"] = get_inequality_operator_from_input(params_copy["inequality"])

        function = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(Constraint(function, None, sport, params_copy))

    def __preprocess(self):
        unary_constraints = list(filter(lambda constraint: constraint.constraint_type == ConstraintType.UNARY,
                                        self.constraints))
        for unary_constraint in unary_constraints:
            for variable in self.variables:
                for option in self.variables[variable]:
                    if not unary_constraint.constraint.function(option):
                        self.variables[variable].remove(option)
            self.constraints.remove(unary_constraint)

    def solve(self):
        # JUST LOOK AT REWRITING THIS - ONE VARIABLE OR MANY?
        self.data["start_time"] = time.time()
        self.__preprocess()

        initial_population_size = 100

        population = [{variable: random.choice(self.variables[variable]) for variable in self.variables} for _ in
                      range(initial_population_size)]

        max_iterations = 5
        epsilon = 0.01  # fitness_threshold
        delta = 0.1  # mutation percentage

        for iteration in range(max_iterations):
            fitness_of_population = [self.__calculate_fitness(assignments) for assignments in population]
            fittest_assignments = [assignments for (assignments, fitness_value) in
                                   zip(population, fitness_of_population) if fitness_value > epsilon]
            print(fitness_of_population)
            new_options = []
            while len(new_options) < len(population) - len(fittest_assignments):
                if len(fittest_assignments) < 2:
                    return None
                parent_1, parent_2 = random.sample(fittest_assignments, 2)
                child = self.__crossover(parent_1, parent_2)
                child = self.__mutate(delta, child)
                new_options.append(child)

            population = fittest_assignments + new_options

        return population

    def __heuristic(self, assignments):

        normalising_factor = sum(optional_constraint_heuristic.params["weight"] for optional_constraint_heuristic in
                                 self.optional_constraints)
        if normalising_factor == 0:
            return 1
        assignments_by_sport_with_tuple = {}
        for assignment in assignments:
            if not (assignments[assignment].sport.name in assignments_by_sport_with_tuple):
                assignments_by_sport_with_tuple[assignments[assignment].sport.name] = (
                    0.0, {assignment: assignments[assignment]})
            else:
                assignments_by_sport_with_tuple[assignments[assignment].sport.name][1][assignment] = assignments[
                    assignment]

        assignments_by_sport_without_tuple = {}
        for assignment in assignments:
            if not (assignments[assignment].sport.name in assignments_by_sport_without_tuple):
                assignments_by_sport_without_tuple[assignments[assignment].sport.name] = {
                    assignment: assignments[assignment]}
            else:
                assignments_by_sport_without_tuple[assignments[assignment].sport.name][assignment] = assignments[
                    assignment]

        score = 0
        for heuristic in self.optional_constraints:
            if heuristic.sport is not None:
                score += take_average_of_heuristics_across_all_sports(self, assignments_by_sport_without_tuple,
                                                                      heuristic)
            else:
                score += heuristic.constraint.function(self, assignments_by_sport_with_tuple)[0]
        return score / normalising_factor

        # return sum(
        #     optional_constraint_heuristic.constraint.function(self, assignments_by_sport)[1] *
        #     optional_constraint_heuristic.params["weight"] for optional_constraint_heuristic in
        #     self.optional_constraints) / normalising_factor

    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(constraint.constraint, assignments)
        return len(conflicts) == 0

    def __calculate_fitness(self, assignments: dict[str, Event]) -> float:
        constraints_broken = 0
        for constraint in self.constraints:
            constraints_broken += len(constraint_check(constraint.constraint, assignments)) > 0

        optional_constraints_score = self.__heuristic(assignments)

        return optional_constraints_score  # / (20 ** constraints_broken)

    def __crossover(self, x: dict[str, Event], y: dict[str, Event]) -> dict[str, Event]:
        # Only differences are venue, date and time
        child = {}
        for variable in x:
            if random.random() < 0.5:
                child[variable] = x[variable]
            else:
                child[variable] = y[variable]
        return child

    def __mutate(self, delta: float, child: dict[str, Event]) -> dict[str, Event]:
        if random.random() > delta:
            return child
        variable_to_mutate = random.choice(list(child.keys()))
        child[variable_to_mutate] = random.choice(self.variables[variable_to_mutate])
        return child

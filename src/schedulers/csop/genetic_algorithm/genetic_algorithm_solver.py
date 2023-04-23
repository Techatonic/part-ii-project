import copy
import math
import os

from multiprocess.pool import Pool
import time
import random

from src.constraints.constraint import Constraint, get_constraint_from_string, ConstraintType
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_optional_constraint_from_string, \
    get_inequality_operator_from_input, take_average_of_heuristics_across_all_sports
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import flatten_events_by_sport_to_dict
from src.schedulers.csp.csp_scheduler import CSPScheduler
from src.schedulers.csp.csp_solver import CSPSolver
from src.schedulers.solver import Solver

from src.sports.sport import Sport


# random.seed(1)

def generate_single_population(sports, data, num_iterations):
    populations = []
    for i in range(num_iterations):
        csp_scheduler = CSPScheduler(CSPSolver, sports, data, False)
        populations.append(csp_scheduler.schedule_events().complete_games["events"])
    return populations


class GeneticAlgorithmSolver(Solver):
    def __init__(self, data=None, forward_check=False, initial_population=None) -> None:
        self.data = data if data is not None else {}

        self.constraints: list[Constraint] = []
        self.optional_constraints: list[Constraint] = []
        self.forward_check: bool = forward_check
        self.variables = {}
        self.initial_population = None if initial_population is None else initial_population

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
        constraint = get_constraint_from_string(function_name)
        self.constraints.append(constraint(variables, sport, copy.deepcopy(params)))

    def add_optional_constraint(self, function_name: str, sport: Sport | None = None, params=None):
        params_copy = copy.deepcopy(params)
        if params_copy is None:
            params_copy = {}
        if not ("weight" in params_copy):
            params_copy["weight"] = 1
        if "inequality" in params_copy:
            params_copy["inequality"] = get_inequality_operator_from_input(params_copy["inequality"])

        constraint = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(constraint(None, sport, params_copy))

    def __preprocess(self):
        unary_constraints = list(filter(lambda constraint: constraint.get_constraint_type() == ConstraintType.UNARY,
                                        self.constraints))
        for unary_constraint in unary_constraints:
            for variable in self.variables:
                for option in self.variables[variable]:
                    if not unary_constraint.eval_constraint({option.id: option}):
                        self.variables[variable].remove(option)
            self.constraints.remove(unary_constraint)

    def __initialise_population(self, initial_population_size):
        if self.initial_population is not None:
            return self.initial_population

        pool_size = os.cpu_count()
        num_iterations = math.ceil(initial_population_size / pool_size)

        inputs = [(self.data['sports'], self.data, num_iterations)] * pool_size

        pool = Pool()
        population = pool.starmap(generate_single_population, inputs)
        population = [item for sublist in population for item in sublist]
        population = population[:initial_population_size]
        return population

    def solve(self, attempt=0):
        if attempt == 5:
            return None
        self.data["start_time"] = time.time()
        self.__preprocess()

        max_iterations = ("genetic_algorithm_iterations" in self.data and self.data[
            "genetic_algorithm_iterations"]) or 500
        initial_population_size = ("initial_population_size" in self.data and self.data[
            "initial_population_size"]) or 250

        epsilon = 0.75  # fitness_threshold
        delta = 0.1  # mutation percentage

        a = time.time()
        population = self.__initialise_population(initial_population_size)
        print("Time taken: ", time.time() - a)

        evaluation_by_iteration = []

        num_fittest_assignments = max(math.ceil(len(population) / 10), 5)

        for iteration in range(max_iterations):
            if iteration % 50 == 0:
                print(f'Iteration # {iteration}')
            fitness_of_population = [self.__calculate_fitness(assignments) for assignments in population]
            fittest_assignments = [assignments for (assignments, fitness_value) in
                                   sorted(zip(population, fitness_of_population), key=lambda x: x[1], reverse=True)][
                                  :num_fittest_assignments]
            # fittest_assignments = [assignments for (assignments, fitness_value) in
            #                        sorted(zip(population, fitness_of_population), key=lambda x: x[1], reverse=True) if
            #                        fitness_value > epsilon]

            if len(fittest_assignments) < 2:
                handle_error("Less than 2 fit assignments", exit_program=False)
                self.initial_population = None
                return self.solve(attempt + 1)

            evaluation_by_iteration.append([iteration, self.__calculate_fitness(fittest_assignments[0])])
            new_options = []
            while len(new_options) < len(population) - len(fittest_assignments):
                parent_1, parent_2 = random.sample(fittest_assignments, 2)
                child = self.__crossover(parent_1, parent_2)
                child = self.__mutate(delta, child)
                new_options.append(child)

            population = fittest_assignments + new_options

        fitness_of_population = [self.__calculate_fitness(assignments) for assignments in population]
        fittest_assignments = [assignments for (assignments, fitness_value) in
                               sorted(zip(population, fitness_of_population), key=lambda x: x[1], reverse=True)][
                              :math.ceil(len(population) / 10)]
        self.data["time_taken"] = time.time() - self.data["start_time"]
        return fittest_assignments[0], self.__calculate_fitness(fittest_assignments[0]), evaluation_by_iteration

    def __heuristic(self, assignments: dict[str, dict[str, Event]]) -> float:
        normalising_factor = sum(
            optional_constraint_heuristic.get_params()["weight"] for optional_constraint_heuristic in
            self.optional_constraints)
        if normalising_factor == 0:
            return 1
        assignments_by_sport_with_tuple = {}
        for sport in assignments:
            assignments_by_sport_with_tuple[sport] = (0, assignments[sport])

        score = 0
        for heuristic in self.optional_constraints:
            if heuristic.get_sport() is not None:
                score += take_average_of_heuristics_across_all_sports(self, assignments,
                                                                      heuristic) * heuristic.get_params()["weight"]
            else:
                score += heuristic.eval_constraint(self, assignments_by_sport_with_tuple)[1] * heuristic.get_params()[
                    "weight"]
        return score / normalising_factor

    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(constraint, assignments)
        return len(conflicts) == 0

    def __calculate_fitness(self, assignments: dict[str, dict[str, Event]]) -> float:
        constraints_broken = 0
        assignments_flatten = flatten_events_by_sport_to_dict(assignments)
        for constraint in self.constraints:
            if constraint.get_sport() is None:
                constraints_broken += len(constraint_check(constraint, assignments_flatten)) > 0
            else:
                sport_name = constraint.get_sport().name
                constraints_broken += len(constraint_check(constraint, assignments[sport_name])) > 0

        optional_constraints_score = self.__heuristic(assignments)

        return optional_constraints_score / (2 ** constraints_broken)

    def __crossover(self, x: dict[str, dict[str, Event]], y: dict[str, dict[str, Event]]) -> dict[
        str, dict[str, Event]]:
        # Only differences are venue, date and time
        child = {}
        for sport in x:
            child[sport] = {}
            for variable in x[sport]:
                if random.random() < 0.5:
                    child[sport][variable] = x[sport][variable]
                else:
                    child[sport][variable] = y[sport][variable]
        return child

    def __mutate(self, delta: float, child: dict[str, dict[str, Event]]) -> dict[str, dict[str, Event]]:
        if random.random() > delta:
            return child
        # Mutate one variable from each sport
        for sport in child:
            variable_to_mutate = random.choice(list(child[sport].keys()))
            child[sport][variable_to_mutate] = random.choice(self.variables[variable_to_mutate])
        return child

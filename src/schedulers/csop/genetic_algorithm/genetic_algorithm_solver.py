import copy
import math
import os

from multiprocess.pool import Pool
import time
import random

from src.constraints.constraint import (
    Constraint,
    get_constraint_from_string,
    ConstraintType,
)
from src.constraints.constraint_checker import single_constraint_check
from src.constraints.optional_constraints import (
    get_optional_constraint_from_string,
    get_inequality_operator_from_input,
)
from src.helper.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import flatten_events_by_sport_to_dict, calculate_fitness
from src.schedulers.csp.csp_scheduler import CSPScheduler
from src.schedulers.csp.csp_solver import CSPSolver
from src.schedulers.solver import Solver

from src.sports.sport import Sport


def generate_population(sports, data, num_iterations):
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
        self.initial_population = (
            None if initial_population is None else initial_population
        )
        self.fitness_values = {}

    def add_variable(self, new_var: str, domain) -> None:
        if new_var in self.variables:
            handle_error("Variable already exists")
        if type(domain) != list:
            handle_error("Domain is not a list")
        self.variables[new_var] = domain

    def get_variables(self) -> dict:
        return self.variables

    def add_constraint(
        self,
        function_name: str,
        variables: list[str] | None = None,
        sport: Sport | None = None,
        params: dict = None,
    ) -> None:
        constraint = get_constraint_from_string(function_name)
        self.constraints.append(constraint(variables, sport, copy.deepcopy(params)))

    def add_optional_constraint(
        self, function_name: str, sport: Sport | None = None, params=None
    ):
        params_copy = copy.deepcopy(params)
        if params_copy is None:
            params_copy = {}
        if not ("weight" in params_copy):
            params_copy["weight"] = 1
        if "inequality" in params_copy:
            params_copy["inequality"] = get_inequality_operator_from_input(
                params_copy["inequality"]
            )

        constraint = get_optional_constraint_from_string(function_name)
        self.optional_constraints.append(constraint(None, sport, params_copy))

    def __preprocess(self):
        unary_constraints = list(
            filter(
                lambda constraint: constraint.get_constraint_type()
                == ConstraintType.UNARY,
                self.constraints,
            )
        )
        for unary_constraint in unary_constraints:
            for variable in self.variables:
                self.variables[variable] = [
                    option
                    for option in self.variables[variable]
                    if single_constraint_check(unary_constraint, option)
                ]
                if len(self.variables[variable]) == 0:
                    handle_error("No solutions found for this input")
            self.constraints.remove(unary_constraint)

    def __initialise_population(self, initial_population_size):
        if self.initial_population is not None:
            return self.initial_population

        pool_size = os.cpu_count()
        num_iterations = math.ceil(initial_population_size / pool_size)

        inputs = [(self.data["sports"], self.data, num_iterations)] * pool_size

        pool = Pool()
        population = pool.starmap(generate_population, inputs)
        population = [item for sublist in population for item in sublist]
        population = population[:initial_population_size]
        return population

    def solve(self, attempt=0):
        if attempt == 5:
            return None
        self.data["start_time"] = time.time()
        self.__preprocess()

        max_iterations = (
            "genetic_algorithm_iterations" in self.data
            and self.data["genetic_algorithm_iterations"]
        ) or 500
        initial_population_size = (
            "initial_population_size" in self.data
            and self.data["initial_population_size"]
        ) or 250

        delta = 0.1  # mutation percentage

        a = time.time()
        population = self.__initialise_population(initial_population_size)

        evaluation_by_iteration = {}

        num_fittest_assignments = max(math.ceil(len(population) / 10), 5)

        self.data["time_taken"] = {}

        for iteration in range(max_iterations):
            fitness_of_population = [
                self.__calculate_fitness(assignments) for assignments in population
            ]
            fittest_assignments = [
                assignments
                for (assignments, fitness_value) in sorted(
                    zip(population, fitness_of_population),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ][:num_fittest_assignments]

            if len(fittest_assignments) < 2:
                handle_error("Less than 2 fit assignments.\nNo solutions found.")
                self.initial_population = None
                return self.solve(attempt + 1)

            new_options = []
            while len(new_options) < len(population) - len(fittest_assignments):
                parent_1, parent_2 = random.sample(fittest_assignments, 2)
                child_1, child_2 = self.__crossover(parent_1, parent_2)
                child_1 = self.__mutate(delta, child_1)
                child_2 = self.__mutate(delta, child_2)
                new_options.append(child_1)
                new_options.append(child_2)

            population = fittest_assignments + new_options
            self.data["time_taken"][iteration + 1] = (
                time.time() - self.data["start_time"]
            )

            fitness_of_population = [
                self.__calculate_fitness(assignments) for assignments in population
            ]
            fittest_assignments = [
                assignments
                for (assignments, fitness_value) in sorted(
                    zip(population, fitness_of_population),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ][: math.ceil(len(population) / 10)]
            evaluation_by_iteration[iteration + 1] = self.__calculate_fitness(
                fittest_assignments[0]
            )

        return (
            fittest_assignments[0],
            self.__calculate_fitness(fittest_assignments[0]),
            evaluation_by_iteration,
            self.data["time_taken"],
        )

    def __calculate_fitness(self, assignments: dict[str, dict[str, Event]]) -> float:
        hashes = []
        events = list(flatten_events_by_sport_to_dict(assignments).values())
        for event in events:
            hashes.append(hash(event))

        hash_value = hash(tuple(hashes))

        if hash_value in self.fitness_values:
            return self.fitness_values[hash_value]

        fitness = calculate_fitness(
            assignments, self.constraints, self.optional_constraints, self, True
        )
        self.fitness_values[hash_value] = fitness
        return fitness

    def __crossover(
        self,
        parent_1: dict[str, dict[str, Event]],
        parent_2: dict[str, dict[str, Event]],
    ) -> tuple[dict[str, dict[str, Event]], dict[str, dict[str, Event]]]:
        list_of_events = sorted(
            [x for sport in parent_1 for x in list(parent_1[sport].keys())]
        )
        split_1 = list_of_events[: len(list_of_events) // 2]

        child_1 = {}
        child_2 = {}
        for sport in parent_1:
            child_1[sport] = {}
            child_2[sport] = {}
            for variable in parent_1[sport]:
                if variable in split_1:
                    child_1[sport][variable] = parent_1[sport][variable]
                    child_2[sport][variable] = parent_2[sport][variable]
                else:
                    child_1[sport][variable] = parent_2[sport][variable]
                    child_2[sport][variable] = parent_1[sport][variable]
        return child_1, child_2

    def __mutate(
        self, delta: float, child: dict[str, dict[str, Event]]
    ) -> dict[str, dict[str, Event]]:
        for sport in child:
            if random.random() < delta:
                variable_to_mutate = random.choice(list(child[sport].keys()))
                child[sport][variable_to_mutate] = random.choice(
                    self.variables[variable_to_mutate]
                )
        return child

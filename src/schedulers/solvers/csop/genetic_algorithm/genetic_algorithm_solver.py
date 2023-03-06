import copy
import math
import time
import random

from src.constraints.constraint import Constraint, get_constraint_from_string, ConstraintType
from src.constraints.constraint_checker import constraint_check
from src.constraints.optional_constraints import get_optional_constraint_from_string, \
    get_inequality_operator_from_input, take_average_of_heuristics_across_all_sports
from src.error_handling.handle_error import handle_error
from src.events.event import Event
from src.helper.helper import widen_events_to_events_by_sport, flatten_events_by_sport_to_dict
from src.schedulers.solvers.csp.csp_scheduler import CSPScheduler
from src.schedulers.solvers.csp.csp_solver import CSPSolver

from src.sports.sport import Sport


# random.seed(1)


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

    def __initialise_population(self):
        initial_population_size = 100
        population = []

        for i in range(initial_population_size):
            csp_scheduler = CSPScheduler(CSPSolver, self.data['sports'], self.data, False)
            result = csp_scheduler.schedule_events().complete_games["events"]
            population.append(result)

        return population

    def solve(self):
        # JUST LOOK AT REWRITING THIS - ONE VARIABLE OR MANY?
        self.data["start_time"] = time.time()
        self.__preprocess()

        population = self.__initialise_population()

        max_iterations = self.data["genetic_algorithm_iterations"]
        epsilon = 0.7  # fitness_threshold
        delta = 0.1  # mutation percentage

        evaluation_by_iteration = []

        for iteration in range(max_iterations):
            fitness_of_population = [self.__calculate_fitness(assignments) for assignments in population]
            # fittest_assignments = [assignments for (assignments, fitness_value) in
            #                        sorted(zip(population, fitness_of_population), key=lambda x: x[1], reverse=True) if
            #                        fitness_value > epsilon]
            fittest_assignments = [assignments for (assignments, fitness_value) in
                                   sorted(zip(population, fitness_of_population), key=lambda x: x[1], reverse=True)][
                                  :math.ceil(len(population) / 10)]

            evaluation_by_iteration.append([iteration, self.__calculate_fitness(fittest_assignments[0])])
            # print("Best Score: ", self.__calculate_fitness(fittest_assignments[0]), end=" " * 10)
            # print("Avg  Score: ",
            #      sum(self.__calculate_fitness(fittest_assignments[i]) for i in range(len(fittest_assignments))) / len(
            #          fittest_assignments), "\n")
            new_options = []
            while len(new_options) < len(population) - len(fittest_assignments):
                if len(fittest_assignments) < 2:
                    return None
                parent_1, parent_2 = random.sample(fittest_assignments, 2)
                child = self.__crossover(parent_1, parent_2)
                child = self.__mutate(delta, child)
                new_options.append(child)

            population = fittest_assignments + new_options

        fitness_of_population = [self.__calculate_fitness(assignments) for assignments in population]
        fittest_assignments = [assignments for (assignments, fitness_value) in
                               sorted(zip(population, fitness_of_population), key=lambda x: x[1], reverse=True)][
                              :math.ceil(len(population) / 10)]
        # print("Eval Score: ", self.__calculate_fitness(fittest_assignments[0]))
        return fittest_assignments[0], self.__calculate_fitness(fittest_assignments[0]), evaluation_by_iteration

    def __heuristic(self, assignments: dict[str, dict[str, Event]]) -> float:
        normalising_factor = sum(optional_constraint_heuristic.params["weight"] for optional_constraint_heuristic in
                                 self.optional_constraints)
        if normalising_factor == 0:
            return 1
        assignments_by_sport_with_tuple = {}
        for sport in assignments:
            assignments_by_sport_with_tuple[sport] = (0, assignments[sport])

        score = 0
        for heuristic in self.optional_constraints:
            if heuristic.sport is not None:
                score += take_average_of_heuristics_across_all_sports(self, assignments,
                                                                      heuristic) * heuristic.params["weight"]
            else:
                score += heuristic.constraint.function(self, assignments_by_sport_with_tuple)[1] * heuristic.params[
                    "weight"]
        return score / normalising_factor

    def __test_constraints(self, assignments, constraints: list[Constraint]) -> bool:
        conflicts = []
        for constraint in constraints:
            conflicts += constraint_check(constraint.constraint, assignments)
        return len(conflicts) == 0

    def __calculate_fitness(self, assignments: dict[str, dict[str, Event]]) -> float:
        constraints_broken = 0
        assignments_flatten = flatten_events_by_sport_to_dict(assignments)
        for constraint in self.constraints:
            if constraint.sport is None:
                constraints_broken += len(constraint_check(constraint.constraint, assignments_flatten)) > 0
            else:
                sport_name = constraint.sport.name
                constraints_broken += len(constraint_check(constraint.constraint, assignments[sport_name])) > 0

        optional_constraints_score = self.__heuristic(assignments)
        if constraints_broken > 0:
            return 0
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

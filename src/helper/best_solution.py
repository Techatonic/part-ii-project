from bisect import insort


class BestSolutions:
    def __init__(self, num_results=10):
        self.best_solutions = []
        # TODO Add this as an input field (curr defined in scheduler) - call it something like 'optimality' and say it
        #  takes longer to run for higher values
        self.num_results = num_results

    def update_bounds(self, heuristic_val: float, assignments):
        insort(self.best_solutions, (heuristic_val, assignments), key=lambda x: x[0])
        while len(self.best_solutions) > self.num_results:
            self.best_solutions.pop(0)
        # print([x[0] for x in self.best_solutions])

    def get_best_solutions(self):
        return self.best_solutions

    def get_worst_bound(self):
        return self.best_solutions[0][0] if len(self.best_solutions) >= self.num_results else -float('inf')

    def is_full(self) -> bool:
        return len(self.best_solutions) >= self.num_results

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            bound: {[x[0] for x in self.best_solutions]},
        \n}}"""

# class BestSolution:
#     def __init__(self):
#         self.__best_solution = None
#
#     def update_best_solution(self, heuristic_val: float, assignments):
#         self.__best_solution = (heuristic_val, assignments)
#
#     def get_best_solution(self):
#         return None if self.__best_solution is None else [self.__best_solution]
#
#     def get_best_solution_score(self):
#         return 0 if self.__best_solution is None else self.__best_solution[0]
#
#     def __str__(self) -> str:
#         return self.__repr__()
#
#     def __repr__(self) -> str:
#         return f"""Bound val: {self.__best_solution[0]}"""
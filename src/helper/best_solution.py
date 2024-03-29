from bisect import insort


class BestSolutions:
    def __init__(self, num_results=10):
        self.best_solutions = []
        self.num_results = num_results

    def update_bounds(self, heuristic_val: float, assignments):
        insort(self.best_solutions, (heuristic_val, assignments), key=lambda x: x[0])
        while len(self.best_solutions) > self.num_results:
            self.best_solutions.pop(0)

    def get_best_solutions(self):
        return self.best_solutions

    def get_worst_bound(self):
        return (
            self.best_solutions[0][0]
            if len(self.best_solutions) >= self.num_results
            else -float("inf")
        )

    def is_full(self) -> bool:
        return len(self.best_solutions) >= self.num_results

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f"""{{
            bound: {[x[0] for x in self.best_solutions]},
        \n}}"""

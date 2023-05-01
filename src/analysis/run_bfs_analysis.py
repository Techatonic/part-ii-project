import copy
import multiprocessing
import sys
import time

import pandas as pd
from matplotlib import pyplot as plt

sys.path.append("/home/danny/Documents/Uni/Year3/Diss/part-ii-project/")

from src.constraints.constraint_checker import constraint_checker
from src.schedulers.constraint_fixing.constraint_fixing_scheduler import ConstraintFixingScheduler
from src.schedulers.constraint_fixing.constraint_fixing_solver import ConstraintFixingSolver
from src.helper.helper import add_global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input_constraint_checker

export_path = "/home/danny/Documents/Uni/Year3/Diss/part-ii-project/examples/outputs/test_output.json"


def run(n, run):
    import_path = "/home/danny/Documents/Uni/Year3/Diss/part-ii-project/examples/inputs/example_input_constraint_checker_" + str(
        n) + ".json"

    input_json = read_and_validate_input(import_path,
                                         '/home/danny/Documents/Uni/Year3/Diss/part-ii-project/schemata/input_schema_constraint_checker.json')
    [sports, events, general_constraints, data] = parse_input_constraint_checker(input_json)
    add_global_variables(sports, data, general_constraints)
    data["general_constraints"] = general_constraints

    # print(n, run)

    default_constraints = {"valid_match_time": {}}
    general_constraints['required'].update(default_constraints)

    conflicts = constraint_checker(sports, events, general_constraints)
    data['conflicts'] = conflicts

    scheduler = ConstraintFixingScheduler(ConstraintFixingSolver, sports, data, False, events, n)
    start_time = time.time()
    complete_games = scheduler.schedule_events().complete_games
    complete_games["time_taken"] = time.time() - start_time
    complete_games["num_fixes"] = n
    # print(f'num_fixes: {n}  -  time taken: {complete_games["time_taken"]}')
    return complete_games


n_range = range(1, 7)  # Range of num_results_to_collect values to check
iterations = range(1, 10)  # Average across 10 tests
inputs = [(n, it) for n in n_range for it in iterations]
pool = multiprocessing.Pool(4)
outputs = pool.starmap(run, inputs)

avg_runtime_by_iteration = {}
avg_nodes_checked = {}
for iteration in n_range:
    avg_runtime_by_iteration[iteration] = []
    avg_nodes_checked[iteration] = []

for result in outputs:
    time_taken = result["time_taken"]
    avg_runtime_by_iteration[result["num_fixes"]].append(time_taken)
    avg_nodes_checked[result["num_fixes"]].append(result["nodes_checked"])

for iteration in avg_runtime_by_iteration:
    avg_runtime_by_iteration[iteration] = sum(avg_runtime_by_iteration[iteration]) / len(
        avg_runtime_by_iteration[iteration])
for iteration in avg_nodes_checked:
    avg_nodes_checked[iteration] = sum(avg_nodes_checked[iteration]) / len(avg_nodes_checked[iteration])

df = pd.DataFrame({
    "num_fixes": list(avg_runtime_by_iteration.keys()),
    "runtimes": list(avg_runtime_by_iteration.values()),
    "nodes_checked": list(avg_nodes_checked.values())
})
print(df.head())

df.to_csv("bfs_analysis.csv")

fig, ax = plt.subplots()
line_1 = ax.plot(df["num_fixes"], df["runtimes"], label="Runtime")
ax.set_xticks([i for i in range(0, n_range.stop)])
ax.set_ylabel("Runtime (s)")
ax.set_xlabel("Num Fixes Required")

ax.legend()

plt.show(block=True)

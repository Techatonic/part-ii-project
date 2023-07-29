import copy
import multiprocessing
import time

import pandas as pd
from matplotlib import pyplot as plt

from src.helper.helper import add_global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input
from src.schedulers.csop.heuristic_backtracking.heuristic_backtracking_scheduler import (
    HeuristicBacktrackingScheduler,
)
from src.schedulers.csop.heuristic_backtracking.heuristic_backtracking_solver import (
    HeuristicBacktrackingSolver,
)

import_path = "examples/inputs/example_input_normal_16.json"
export_path = "examples/outputs/test_output.json"
input_json = read_and_validate_input(import_path, "schemata/input_schema.json")

[sports, general_constraints, data] = parse_input(input_json)
add_global_variables(sports, data, general_constraints)
data["general_constraints"] = general_constraints


def run(n, run):
    print(n, run)
    data["num_results_to_collect"] = n
    _data = copy.deepcopy(data)
    scheduler = HeuristicBacktrackingScheduler(
        HeuristicBacktrackingSolver, sports, _data, False
    )
    start_time = time.time()
    complete_games = scheduler.schedule_events().complete_games
    complete_games["time_taken"] = time.time() - start_time
    complete_games["num_results_to_collect"] = n
    return complete_games


n_range = range(5, 51, 5)  # Range of num_results_to_collect values to check
iterations = range(1, 101)  # Average across 100 tests
inputs = [(n, it) for n in n_range for it in iterations]
pool = multiprocessing.Pool(8)
outputs = pool.starmap(run, inputs)

avg_eval_score_by_iteration = {}
for iteration in n_range:
    avg_eval_score_by_iteration[iteration] = []

avg_runtime_by_iteration = {}
for iteration in n_range:
    avg_runtime_by_iteration[iteration] = []

for result in outputs:
    num_results_to_collect = result["num_results_to_collect"]
    eval_score = result["eval_score"]
    time_taken = result["time_taken"]
    avg_eval_score_by_iteration[num_results_to_collect].append(eval_score)
    avg_runtime_by_iteration[num_results_to_collect].append(time_taken)


for iteration in avg_eval_score_by_iteration:
    avg_eval_score_by_iteration[iteration] = sum(
        avg_eval_score_by_iteration[iteration]
    ) / len(avg_eval_score_by_iteration[iteration])
for iteration in avg_runtime_by_iteration:
    avg_runtime_by_iteration[iteration] = sum(
        avg_runtime_by_iteration[iteration]
    ) / len(avg_runtime_by_iteration[iteration])

df = pd.DataFrame(
    {
        "num_results_to_collect": list(avg_eval_score_by_iteration.keys()),
        "avg_eval_score": list(avg_eval_score_by_iteration.values()),
        "runtimes": list(avg_runtime_by_iteration.values()),
    }
)

df.to_csv("heuristic_backtracking_analysis.csv")

fig, ax = plt.subplots()
line_1 = ax.plot(df["num_results_to_collect"], df["avg_eval_score"], label="Eval Score")
ax.set_xticks([i for i in range(0, n_range.stop, 5)])
ax.set_ylabel("Eval Score")
ax.set_xlabel("Num Results to Collect")

ax1 = ax.twinx()
line_2 = ax1.plot(
    df["num_results_to_collect"], df["runtimes"], label="Runtime (s)", color="orange"
)
ax1.set_ylabel("Runtime (s)")

lns = line_1 + line_2
labs = [l.get_label() for l in lns]
ax.legend(lns, labs, loc=0)

plt.tight_layout()
plt.savefig("heuristic_backtracking_analysis_graph.pdf")

plt.show(block=True)

import os
from argparse import ArgumentParser
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import main

parser = ArgumentParser('Analysis on Iteration vs Performance of Genetic Algorithms')

iterations = 100
ga_iterations = 1000

evaluation_scores = np.array([], dtype=float)

avg_eval_score_by_iteration = {}
for iteration in range(ga_iterations):
    avg_eval_score_by_iteration[iteration] = []

for run in range(iterations):
    start_time = time.time()

    import_path = "/home/danny/Documents/Uni/Year3/Diss/part-ii-project/examples/inputs/example_input.json"
    export_path = "/home/danny/Documents/Uni/Year3/Diss/part-ii-project/examples/outputs/test_output.json"

    result = main.main(import_path, export_path, 0, False, False, ga_iterations, False)
    if result is None:
        continue
    result_eval = result.complete_games["eval_score"]
    eval_by_iteration = result.complete_games["eval_by_iteration"]
    for [iteration, score] in eval_by_iteration:
        avg_eval_score_by_iteration[iteration].append(score)

    print("Iteration # ", run + 1, " " * 6, "Final Evaluation Score: ", result_eval)
    evaluation_scores = np.append(evaluation_scores, result_eval)

# df = pd.DataFrame({
#     "iterations": iterations,
#     "evaluation_score": evaluation_scores
# })
#
# print(df)
# ax = df.plot.line(x="iterations", y="evaluation_score")
# ax.set_xticks([0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000])
# plt.show(block=True)

for iteration in avg_eval_score_by_iteration:
    avg_eval_score_by_iteration[iteration] = sum(avg_eval_score_by_iteration[iteration]) / len(
        avg_eval_score_by_iteration[iteration])

df = pd.DataFrame({
    "iterations": list(avg_eval_score_by_iteration.keys()),
    "avg_eval_score": list(avg_eval_score_by_iteration.values())
})
print(df)
ax = df.plot.line(x="iterations", y="avg_eval_score")
ax.set_xticks([i for i in range(0, ga_iterations + 1, 25)])
plt.show(block=True)

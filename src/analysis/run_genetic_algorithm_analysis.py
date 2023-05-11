import copy
import multiprocessing
import time
from argparse import ArgumentParser
from itertools import repeat

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from textwrap import wrap

from src.helper.handle_error import handle_error
from src.helper.helper import add_global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input
from src.schedulers.csop.genetic_algorithm.genetic_algorithm_scheduler import GeneticAlgorithmScheduler
from src.schedulers.csop.genetic_algorithm.genetic_algorithm_solver import GeneticAlgorithmSolver
from src.schedulers.csp.csp_scheduler import CSPScheduler
from src.schedulers.csp.csp_solver import CSPSolver

import_path = "examples/inputs/example_input_normal_16.json"
export_path = "examples/outputs/test_output.json"

input_json = read_and_validate_input(import_path, 'schemata/input_schema.json')
[sports, general_constraints, data] = parse_input(input_json)
add_global_variables(sports, data, general_constraints)
data["general_constraints"] = general_constraints


def compare_iterations_inner(n):
    _data = copy.deepcopy(data)
    scheduler = GeneticAlgorithmScheduler(GeneticAlgorithmSolver, sports, _data, False)
    result = scheduler.schedule_events()
    return result.complete_games


def compare_iterations():
    iterations = 4
    ga_iterations = 10
    data["genetic_algorithm_iterations"] = ga_iterations
    data["initial_population_size"] = 10

    pool = multiprocessing.Pool(4)
    outputs = pool.map(compare_iterations_inner, range(iterations))

    avg_eval_score_by_iteration = {}
    for iteration in range(ga_iterations):
        avg_eval_score_by_iteration[iteration] = []

    avg_runtime_by_iteration = {}
    for iteration in range(ga_iterations):
        avg_runtime_by_iteration[iteration] = []

    for result in outputs:
        eval_by_iteration = result["eval_by_iteration"]
        time_taken_by_iteration = result["time_taken_by_iteration"]
        for iteration, score in eval_by_iteration.items():
            avg_eval_score_by_iteration[iteration].append(score)
        for iteration, time_taken in time_taken_by_iteration.items():
            avg_runtime_by_iteration[iteration].append(time_taken)

    for iteration in avg_eval_score_by_iteration:
        avg_eval_score_by_iteration[iteration] = sum(avg_eval_score_by_iteration[iteration]) / len(
            avg_eval_score_by_iteration[iteration])
    for iteration in avg_runtime_by_iteration:
        avg_runtime_by_iteration[iteration] = sum(avg_runtime_by_iteration[iteration]) / len(
            avg_runtime_by_iteration[iteration])

    df = pd.DataFrame({
        "iterations": list(avg_eval_score_by_iteration.keys()),
        "avg_eval_score": list(avg_eval_score_by_iteration.values()),
        "runtimes": list(avg_runtime_by_iteration.values())
    })

    df.to_csv("ga_iterations_analysis.csv", index_label="GA Iterations")

    fig, ax = plt.subplots()
    line_1 = ax.plot(df["iterations"], df["avg_eval_score"], label="Eval Score")
    ax.set_xticks([i for i in range(0, ga_iterations + 1, 25)])
    ax.set_ylabel("Eval Score")
    ax.set_xlabel("GA Iterations")

    ax1 = ax.twinx()
    line_2 = ax1.plot(df['iterations'], df['runtimes'], label="Runtime (s)", color="orange")
    ax1.set_ylabel("Runtime (s)")

    lns = line_1 + line_2
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc=0)

    plt.show(block=True)


def compare_population_size_run(run, populations, ga_iterations):
    run_start_time = time.time()
    scores = []
    initial_population = [initialise_population(run) for _ in range(populations[-1])]
    for size in populations:
        data["genetic_algorithm_iterations"] = ga_iterations
        data["initial_population_size"] = size
        scheduler = GeneticAlgorithmScheduler(GeneticAlgorithmSolver, sports, data, False,
                                              initial_population=initial_population[:size])
        result = scheduler.schedule_events()
        if result is None:
            continue
        result_eval = result.complete_games["eval_score"]

        print("Run #", run + 1, " " * 4, "population size: ", size, " " * 4, "eval score: ", result_eval)
        scores.append([size, result_eval])

    run_end_time = time.time()
    print("Runtime for run #", run + 1, ": ", run_end_time - run_start_time)
    return scores


def compare_population_size():
    iterations = 64
    ga_iterations = 250
    populations = [50, 60, 70, 80, 90, 100, 125, 150, 175, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800,
                   900, 1000]

    avg_eval_score_by_population_size = {}
    for size in populations:
        avg_eval_score_by_population_size[size] = []

    pool = multiprocessing.Pool(4)
    outputs = list(zip(*pool.starmap(compare_population_size_run,
                                     zip(range(iterations), repeat(populations), repeat(ga_iterations)))))

    for size_result in list(outputs):
        for run in size_result:
            avg_eval_score_by_population_size[run[0]].append(run[1])

    for size in avg_eval_score_by_population_size:
        avg_eval_score_by_population_size[size] = sum(avg_eval_score_by_population_size[size]) / len(
            avg_eval_score_by_population_size[size])

    df = pd.DataFrame({
        "population_size": list(avg_eval_score_by_population_size.keys()),
        "avg_eval_score": list(avg_eval_score_by_population_size.values())
    })

    ax = df.plot.line(x="population_size", y="avg_eval_score")
    ax.set_xticks(list(range(0, 1001, 50)))
    plt.show(block=True)


def initialise_population(run):
    csp_scheduler = CSPScheduler(CSPSolver, sports, data, False)
    result = csp_scheduler.schedule_events().complete_games["events"]
    return result


def compare_iterations_and_population_size_run(run, populations, ga_iterations):
    initialise_population_start_time = time.time()
    initial_population = [initialise_population(run) for _ in range(max(populations))]
    initialise_population_end_time = time.time()
    initialise_time = (initialise_population_end_time - initialise_population_start_time) / max(populations)

    run_start_time = time.time()
    scores = []
    for size in populations:
        # for iterations in ga_iterations:
        data["genetic_algorithm_iterations"] = max(ga_iterations)
        data["initial_population_size"] = size
        scheduler = GeneticAlgorithmScheduler(GeneticAlgorithmSolver, sports, data, False,
                                              initial_population=initial_population[:size])
        result = scheduler.schedule_events()
        if result is None:
            continue
        time_taken = result.complete_games["time_taken"]
        eval_by_iteration = result.complete_games["eval_by_iteration"]
        time_taken_by_iteration = result.complete_games["time_taken_by_iteration"]

        print("Run # ", run + 1, " " * 4, "Initial Population: ", size, " " * 4, " " * 4, "Time Taken: ", time_taken)
        for key in eval_by_iteration:
            scores.append([size, key, eval_by_iteration[key], time_taken_by_iteration[key] + initialise_time * size])

    run_end_time = time.time()
    print("Runtime for run #", run + 1, ": ", run_end_time - run_start_time)
    return scores


def draw_heatmap(data_to_show, cmap, x_labels, y_labels, title, x_title, y_title, x_ticks=None, y_ticks=None,
                 colorbar_label=None):
    fig = plt.figure(figsize=(20, 10))
    ax = plt.gca()
    colormesh = ax.pcolormesh(x_labels, y_labels, data_to_show, cmap=cmap, linewidths=0.1)
    x_ticks = x_labels if x_ticks is None else x_ticks
    y_ticks = y_labels if y_ticks is None else y_ticks

    tick_positions_y = []
    for position in range(len(y_ticks) - 1):
        tick_positions_y.append(y_ticks[position] + (y_ticks[position + 1] - y_ticks[position]) / 2)

    ax.set_xticks(x_ticks)
    ax.set_yticks(tick_positions_y, y_ticks[:-1])
    colorbar = fig.colorbar(colormesh, ax=ax)
    colorbar.ax.set_ylabel(colorbar_label, rotation=270, labelpad=15)

    ax.set_xlabel(x_title)
    ax.set_ylabel(y_title)
    ax.set_title("\n".join(wrap(title, 40)))
    fig.tight_layout()
    plt.subplots_adjust(0.05, 0.05, 0.95, 0.95)
    plt.savefig("ga_heatmap_" + title + ".pdf", bbox_inches='tight')
    plt.show()


def compare_iterations_and_population_size():
    iterations = 25
    ga_iterations = [i for i in range(1, 101)]
    populations = [25, 50, 75, 100, 200, 300]

    results = {}
    for size in populations:
        results[size] = {}
        for iteration in ga_iterations:
            results[size][iteration] = []

    inputs = []
    for iteration in range(iterations):
        inputs.append([iteration, populations, ga_iterations])

    pool = multiprocessing.Pool(8)
    outputs = list(zip(*pool.starmap(compare_iterations_and_population_size_run, inputs)))

    eval_scores = [[[] for j in range(len(ga_iterations))] for i in range(len(populations))]
    runtimes = [[[] for j in range(len(ga_iterations))] for i in range(len(populations))]

    avg_eval_scores = [[0.0 for j in range(len(ga_iterations))] for i in range(len(populations))]
    avg_runtimes = [[0.0 for j in range(len(ga_iterations))] for i in range(len(populations))]
    for size_result in outputs:
        for size_iteration_result in size_result:
            x = populations.index(size_iteration_result[0])
            y = ga_iterations.index(size_iteration_result[1])
            eval_scores[x][y].append(size_iteration_result[2])
            runtimes[x][y].append(size_iteration_result[3])

    for size in range(len(eval_scores)):
        for size_iteration in range(len(eval_scores[size])):
            avg_eval_score = sum(eval_scores[size][size_iteration]) / len(
                eval_scores[size][size_iteration])
            avg_eval_scores[size][size_iteration] = round(avg_eval_score, 3)

            avg_runtime = sum(runtimes[size][size_iteration]) / len(
                runtimes[size][size_iteration])
            avg_runtimes[size][size_iteration] = round(avg_runtime, 3)

    df = pd.DataFrame(avg_eval_scores, columns=ga_iterations, index=populations)
    df.to_csv("./avg_eval_score.csv", index_label="Population Size")

    df = pd.DataFrame(avg_runtimes, columns=ga_iterations, index=populations)
    df.to_csv("./avg_runtimes.csv", index_label="Population Size")

    avg_performance_per_second = np.divide(avg_eval_scores, avg_runtimes)
    df = pd.DataFrame(avg_performance_per_second, columns=ga_iterations, index=populations)
    df.to_csv("./avg_performance_per_second.csv", index_label="Population Size")

    cmap = LinearSegmentedColormap.from_list('rg', ["darkred", "red", "lightcoral", "palegreen", "green", "darkgreen"],
                                             N=256)

    inverse_cmap = LinearSegmentedColormap.from_list('gr', ["darkgreen", "green", "palegreen", "lightcoral", "red",
                                                            "darkred"],
                                                     N=256)

    draw_heatmap(avg_eval_scores, cmap, ga_iterations, populations,
                 "Heatmap of Population size and GA Iterations vs Performance", "Genetic Algorithm Iterations",
                 "Population Size", None, None, "Evaluation Score")
    draw_heatmap(avg_runtimes, inverse_cmap, ga_iterations, populations,
                 "Heatmap of Population size and GA Iterations vs Runtime", "Genetic Algorithm Iterations",
                 "Population Size", None, None, "Runtime (s)")
    draw_heatmap(avg_performance_per_second, cmap, ga_iterations, populations,
                 "Heatmap of Population and GA Iterations vs Performance per Second", "Genetic Algorithm Iterations",
                 "Population Size", None, None, "Evaluation Score / Second")


parser = ArgumentParser('Analysis of Genetic Algorithms')
parser.add_argument("-i", action='store_true', help="iterations vs performance")
parser.add_argument("-ip", action='store_true', help="initial population size vs performance")
parser.add_argument("-iip", action='store_true', help="initial population size + iterations vs performance")

args = None
try:
    args = parser.parse_args()
except:
    handle_error("Invalid input")

if args.i + args.ip + args.iip != 1:
    raise Exception
if args.i:
    compare_iterations()
if args.ip:
    compare_population_size()

if args.iip:
    compare_iterations_and_population_size()

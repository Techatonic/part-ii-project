import math
import multiprocessing
import pprint
import time
from argparse import ArgumentParser
from itertools import repeat

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

from src.helper.helper import add_global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input
from src.schedulers.solvers.csop.genetic_algorithm.genetic_algorithm_scheduler import GeneticAlgorithmScheduler
from src.schedulers.solvers.csop.genetic_algorithm.genetic_algorithm_solver import GeneticAlgorithmSolver
from src.schedulers.solvers.csp.csp_scheduler import CSPScheduler
from src.schedulers.solvers.csp.csp_solver import CSPSolver

import_path = "/home/danny/Documents/Uni/Year3/Diss/part-ii-project/examples/inputs/example_input.json"
export_path = "/home/danny/Documents/Uni/Year3/Diss/part-ii-project/examples/outputs/test_output.json"

input_json = read_and_validate_input(import_path, 'src/input_handling/input_schema.json')
[sports, general_constraints, data] = parse_input(input_json)
add_global_variables(sports, data, general_constraints)
data["general_constraints"] = general_constraints


def compare_iterations():
    iterations = 100
    ga_iterations = 1000

    avg_eval_score_by_iteration = {}
    for iteration in range(ga_iterations):
        avg_eval_score_by_iteration[iteration] = []

    for run in range(iterations):
        data["genetic_algorithm_iterations"] = ga_iterations
        data["initial_population_size"] = 250
        scheduler = GeneticAlgorithmScheduler(GeneticAlgorithmSolver, sports, data, False)
        result = scheduler.schedule_events()
        if result is None:
            continue
        result_eval = result.complete_games["eval_score"]
        eval_by_iteration = result.complete_games["eval_by_iteration"]
        for [iteration, score] in eval_by_iteration:
            avg_eval_score_by_iteration[iteration].append(score)

        print("Iteration # ", run + 1, " " * 6, "Final Evaluation Score: ", result_eval)

    for iteration in avg_eval_score_by_iteration:
        avg_eval_score_by_iteration[iteration] = sum(avg_eval_score_by_iteration[iteration]) / len(
            avg_eval_score_by_iteration[iteration])

    df = pd.DataFrame({
        "iterations": list(avg_eval_score_by_iteration.keys()),
        "avg_eval_score": list(avg_eval_score_by_iteration.values())
    })
    print(df.head())
    ax = df.plot.line(x="iterations", y="avg_eval_score")
    ax.set_xticks([i for i in range(0, ga_iterations + 1, 25)])
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

        # print("Iteration # ", run + 1, " " * 4, size, " " * 4, "eval_score: ", result_eval)
        print("Run #", run + 1, " " * 4, "population size: ", size, " " * 4, "eval score: ", result_eval)
        scores.append([size, result_eval])

    run_end_time = time.time()
    print("Runtime for run #", run + 1, ": ", run_end_time - run_start_time)
    return scores


def compare_population_size():
    total_start_time = time.time()
    # iterations = 64
    # ga_iterations = 250
    # populations = [50, 60, 70, 80, 90, 100, 125, 150, 175, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800,
    #                900, 1000]

    iterations = 4
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

    print(avg_eval_score_by_population_size)
    for size in avg_eval_score_by_population_size:
        avg_eval_score_by_population_size[size] = sum(avg_eval_score_by_population_size[size]) / len(
            avg_eval_score_by_population_size[size])

    df = pd.DataFrame({
        "population_size": list(avg_eval_score_by_population_size.keys()),
        "avg_eval_score": list(avg_eval_score_by_population_size.values())
    })
    print(df.head())

    total_end_time = time.time()
    print("\nTotal Runtime: ", total_end_time - total_start_time)

    ax = df.plot.line(x="population_size", y="avg_eval_score")
    ax.set_xticks(list(range(0, 1001, 50)))
    plt.show(block=True)


def initialise_population(run):
    csp_scheduler = CSPScheduler(CSPSolver, sports, data, False)
    result = csp_scheduler.schedule_events().complete_games["events"]
    print("Generated Population #", run)
    return result


def compare_iterations_and_population_size_run(run, populations, ga_iterations):
    initial_population = [initialise_population(run) for _ in range(max(populations))]

    run_start_time = time.time()
    scores = []
    for size in populations:
        for iterations in ga_iterations:
            data["genetic_algorithm_iterations"] = iterations
            data["initial_population_size"] = size
            scheduler = GeneticAlgorithmScheduler(GeneticAlgorithmSolver, sports, data, False,
                                                  initial_population=initial_population[:size])
            result = scheduler.schedule_events()
            if result is None:
                continue
            result_eval = result.complete_games["eval_score"]
            time_taken = result.complete_games["time_taken"]

            print("Run # ", run + 1, " " * 4, "Initial Population: ", size, " " * 4, "ga_iterations: ", iterations,
                  " " * 4, "eval_score: ", result_eval, " " * 4, "Time Taken: ", time_taken)
            scores.append([size, iterations, result_eval, time_taken])

    run_end_time = time.time()
    print("Runtime for run #", run + 1, ": ", run_end_time - run_start_time)
    return scores


def compare_iterations_and_population_size():
    total_start_time = time.time()
    iterations = 16
    ga_iterations = [25, 50, 100, 250, 500, 750, 1000]
    populations = [25, 50, 100, 250, 500, 750, 1000]
    # iterations = 2
    # ga_iterations = [50, 500, 1000]
    # populations = [50, 500, 1000]

    results = {}
    for size in populations:
        results[size] = {}
        for iteration in ga_iterations:
            results[size][iteration] = []

    inputs = []
    for iteration in range(iterations):
        inputs.append([iteration, populations, ga_iterations])

    pool = multiprocessing.Pool(4)
    outputs = list(zip(*pool.starmap(compare_iterations_and_population_size_run, inputs)))
    # outputs = list(compare_iterations_and_population_size_run(*input_fields) for input_fields in inputs)

    eval_scores = [[[] for j in range(len(ga_iterations))] for i in range(len(populations))]
    runtimes = [[[] for j in range(len(ga_iterations))] for i in range(len(populations))]

    avg_eval_scores = [[0.0 for j in range(len(ga_iterations))] for i in range(len(populations))]
    avg_runtimes = [[0.0 for j in range(len(ga_iterations))] for i in range(len(populations))]
    print("\n")
    for size_result in outputs:
        for size_iteration_result in size_result:
            x = populations.index(size_iteration_result[0])
            y = ga_iterations.index(size_iteration_result[1])
            print(size_iteration_result)
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

    pprint.pprint(avg_eval_scores)

    df = pd.DataFrame(avg_eval_scores, columns=ga_iterations, index=populations)
    df.to_csv("./avg_eval_score.csv")

    print(df)

    df = pd.DataFrame(avg_runtimes, columns=ga_iterations, index=populations)
    df.to_csv("./avg_runtimes.csv")

    print(df)

    fig, (ax1, ax2) = plt.subplots(2, figsize=(25, 25))
    c = ["darkred", "red", "lightcoral", "palegreen", "green", "darkgreen"]
    v = [0, .675, .72, 0.75, .8, 1]
    l = list(zip(v, c))
    cmap = LinearSegmentedColormap.from_list('rg', l, N=256)

    # runtime_v = [0, 5, 10, 20, 50, 1000]
    # inverse_l = list(zip(runtime_v, c[::-1]))
    # inverse_cmap = LinearSegmentedColormap.from_list('rg', inverse_l, N=256)
    inverse_cmap = LinearSegmentedColormap.from_list('gr', ["darkgreen", "g", "r", "darkred"], N=256)

    im = ax1.imshow(avg_eval_scores, cmap=cmap)

    # Show all ticks and label them with the respective list entries
    ax1.set_yticks(np.arange(len(populations)), labels=populations)
    ax1.set_xticks(np.arange(len(ga_iterations)), labels=ga_iterations)

    ax1.set_ylabel("Population Size")
    ax1.set_xlabel("GA Iterations")

    # Loop over data dimensions and create text annotations.
    for i in range(len(populations)):
        for j in range(len(ga_iterations)):
            text = ax1.text(j, i, avg_eval_scores[i][j],
                            ha="center", va="center", color="w")

    # Runtime graph
    ax1.set_title("Heatmap of Population size and GA Iterations vs Performance")

    im = ax2.imshow(avg_runtimes, cmap=inverse_cmap)

    # Show all ticks and label them with the respective list entries
    ax2.set_xticks(np.arange(len(ga_iterations)), labels=ga_iterations)
    ax2.set_yticks(np.arange(len(populations)), labels=populations)

    # Loop over data dimensions and create text annotations.
    for i in range(len(populations)):
        for j in range(len(ga_iterations)):
            text = ax2.text(j, i, avg_runtimes[i][j],
                            ha="center", va="center", color="w")

    ax2.set_title("Heatmap of Population size and GA Iterations vs Runtime")
    ax2.set_ylabel("Population Size")
    ax2.set_xlabel("GA Iterations")

    fig.subplots_adjust(hspace=1)
    # fig.tight_layout()

    total_end_time = time.time()
    print("\nTotal Runtime: ", total_end_time - total_start_time)

    plt.show()


parser = ArgumentParser('Analysis of Genetic Algorithms')
parser.add_argument("-i", action='store_true', help="iterations vs performance")
parser.add_argument("-ip", action='store_true', help="initial population size vs performance")
parser.add_argument("-iip", action='store_true', help="initial population size + iterations vs performance")

args = None
try:
    args = parser.parse_args()
except:
    print("Invalid input")
    exit()
if args.i + args.ip + args.iip != 1:
    raise Exception
if args.i:
    compare_iterations()
if args.ip:
    compare_population_size()

if args.iip:
    compare_iterations_and_population_size()

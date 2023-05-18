import main
import copy
import json
import sys
import multiprocessing
from multiprocessing import Queue

sys.path.append("")


inputs = [
    "examples/inputs/example_input_tight_8.json",
    "examples/inputs/example_input_tight_16.json",
    "examples/inputs/example_input_tight_32.json",
    "examples/inputs/example_input_normal_8.json"
    "examples/inputs/example_input_normal_16.json"
    "examples/inputs/example_input_normal_32.json"
]

base_args = [
    "main.py",
    "--import_path",
    "",
    "--export_path",
    "examples/outputs/test_output.json",
]
algorithms = {
    "backtracking": ['-b'],
    "heuristic_backtracking": ['-hb', '25'],
    "genetic_algorithm": ['-g', '100', '75'],
    "base": ['-m'],
}

num_runs = 10
timeout_time = 1800

results = {}


def call_main(queue):
    result = main.main()
    queue.put(copy.deepcopy(result.complete_games))


for algorithm in algorithms:
    results[algorithm] = {}
    should_break = False
    for import_path in range(len(inputs)):
        if should_break:
            results[algorithm][import_path] = {
                "time_taken": "N/A",
                "eval_score": "N/A"
            }
            continue
        runtimes = []
        eval_scores = []
        for iteration in range(num_runs):
            base_args[2] = inputs[import_path]
            sys.argv = base_args + algorithms[algorithm]

            Q = Queue()
            p = multiprocessing.Process(
                target=call_main, name="main", args=(Q,))
            p.start()
            p.join(timeout=timeout_time)

            if p.is_alive():
                p.terminate()
                p.join()

                print(f'Failed to finish in {timeout_time} seconds')
                runtimes += ["N/A"] * (num_runs - iteration)
                eval_scores += ["N/A"] * (num_runs - iteration)
                should_break = True
                break

            result = Q.get()

            runtimes.append(result['time_taken'])
            eval_scores.append(result['eval_score'])

        if "N/A" in runtimes:
            results[algorithm][import_path] = {
                "time_taken": "N/A",
                "eval_score": "N/A"
            }
        else:
            results[algorithm][import_path] = {
                "time_taken": sum(runtimes) / len(runtimes),
                "eval_score": sum(eval_scores) / len(eval_scores)
            }

with open('compare_algorithms_result.json', 'w') as fp:
    json.dump(results, fp)

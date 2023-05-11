"""
    A script for generating a solution to a CST scheduling problem
"""
import time
import os
from argparse import ArgumentParser

from src.constraints.constraint_checker import constraint_checker
from src.helper.handle_error import handle_error
from src.helper.helper import add_global_variables
from src.input_handling.input_reader import read_and_validate_input
from src.input_handling.parse_input import parse_input, parse_input_constraint_checker
from src.schedulers.constraint_fixing.constraint_fixing_scheduler import ConstraintFixingScheduler
from src.schedulers.constraint_fixing.constraint_fixing_solver import ConstraintFixingSolver
from src.schedulers.csop.heuristic_backtracking.heuristic_backtracking_scheduler import HeuristicBacktrackingScheduler
from src.schedulers.csop.heuristic_backtracking.heuristic_backtracking_solver import HeuristicBacktrackingSolver
from src.schedulers.csop.genetic_algorithm.genetic_algorithm_scheduler import GeneticAlgorithmScheduler
from src.schedulers.csop.genetic_algorithm.genetic_algorithm_solver import GeneticAlgorithmSolver
from src.schedulers.csp.csp_scheduler import CSPScheduler
from src.schedulers.csp.csp_solver import CSPSolver
from src.schedulers.base.base_solver import ModuleSolver


def main():
    parser = ArgumentParser('Automated Event Scheduler')
    parser.add_argument("--import_path", required=True, type=str, help="read json input from this path")
    parser.add_argument("--export_path", required=False, type=str, help="export json output to this path")
    parser.add_argument("-c", required=False, type=int, metavar='N',
                        help="run input_path on constraint checker and allow up to N changed events")
    parser.add_argument("-m", action='store_true', help="run on CSP base solver")
    parser.add_argument("-b", action='store_true', help="run on CSP backtracking solver")
    parser.add_argument("-hb", required=False, type=int, metavar='N',
                        help="run on CSOP heuristic_backtracking solver using N schedules for each sport")
    parser.add_argument("-g", required=False, type=int, nargs=2, metavar=('P', 'G'),
                        help="run on CSOP genetic algorithm solver with iniital population of size P and G generations")
    parser.add_argument("-forward_check", action='store_true', help="run forward checking algorithm on solver")

    args = parser.parse_args()

    if not os.path.exists(args.import_path):
        handle_error("Path does not exist")

    if (args.c is not None) + args.m + args.b + (args.hb is not None) + (args.g is not None) != 1:
        handle_error(
            "Must select exactly one of constraint checker, module solver, backtracking solver, heuristic backtracking solver and genetic algorithm solver")

    if args.c and args.c < 0 or args.hb and args.hb < 0 or args.g and any(x < 0 for x in args.g):
        handle_error("Negative arguments are not permitted")

    start_time = time.time()
    result = None
    if args.c:
        result = run_constraint_checker(args.import_path, args.export_path, args.c)
    else:
        result = run_solver(args.import_path, args.m, args.b, args.hb,
                            args.g, args.forward_check, args.export_path)

    end_time = time.time()
    result.complete_games["time_taken"] = end_time - start_time
    return result


def run_constraint_checker(input_path: str, export_path: str | None = None, num_changes=1):
    input_json = read_and_validate_input(input_path, 'schemata/input_schema_constraint_checker.json')

    [sports, events, general_constraints, data] = parse_input_constraint_checker(input_json)
    add_global_variables(sports, data, general_constraints)

    default_constraints = {"valid_match_time": {}}
    general_constraints['required'].update(default_constraints)

    conflicts = constraint_checker(sports, events, general_constraints)

    if len(conflicts) == 0:
        print("No conflicts found - all constraints are satisfied")
    else:
        handle_error("Conflicts found - See below:", exit_program=False)
        for conflict in conflicts:
            conflict_str = conflict[0].ljust(35) + str(conflict[1])
            handle_error(conflict_str, exit_program=False)
        data['conflicts'] = conflicts

        scheduler = ConstraintFixingScheduler(ConstraintFixingSolver, sports, data, False, events, num_changes)

        result = scheduler.schedule_events()
        if result is None:
            handle_error("No results found")

        if export_path is not None:
            try:
                result.export(export_path)

            except Exception as e:
                print(e)
                handle_error("Export failed. Please try again ensuring a valid output path is given")
        else:
            print("No export path given")

    return result


def run_solver(input_path: str, use_python_module: bool, use_backtracking_solver: bool,
               use_heuristic_backtracking_solver: int, use_genetic_algorithm: list | None,
               forward_check: bool, export_path: str | None = None):
    input_json = read_and_validate_input(input_path, 'schemata/input_schema.json')

    [sports, general_constraints, data] = parse_input(input_json)
    add_global_variables(sports, data, general_constraints)
    data["general_constraints"] = general_constraints

    solver = None
    scheduler = None
    if use_python_module:  # Base solver
        solver = ModuleSolver
        scheduler = CSPScheduler
    elif use_heuristic_backtracking_solver:  # heuristic_backtracking CSOP solver
        solver = HeuristicBacktrackingSolver
        scheduler = HeuristicBacktrackingScheduler
        data['num_results_to_collect'] = use_heuristic_backtracking_solver
    elif use_genetic_algorithm:  # genetic_algorithm CSOP solver
        solver = GeneticAlgorithmSolver
        scheduler = GeneticAlgorithmScheduler
        data["initial_population_size"] = use_genetic_algorithm[0]
        data["genetic_algorithm_iterations"] = use_genetic_algorithm[1]
    elif use_backtracking_solver:  # CSP solver
        solver = CSPSolver
        scheduler = CSPScheduler
    else:
        handle_error("No scheduler selected")

    scheduler = scheduler(solver, sports, data, forward_check)
    result = scheduler.schedule_events()

    if result is None:
        handle_error("No results found")

    if export_path is not None:
        try:
            result.export(export_path)

        except Exception as e:
            print(e)
            handle_error("Export failed. Please try again ensuring a valid output path is given")

    return result


if __name__ == "__main__":
    main()

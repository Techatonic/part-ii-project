import sys


sys.path.append("./")

import main
import json

import pytest
import hashlib
from jsonschema.exceptions import ValidationError, SchemaError
from jsonschema.validators import validate
import copy


base_args = [
    "main.py",
    "--import_path",
    "examples/inputs/example_input_very_simple.json",
    "--export_path",
    "examples/outputs/test_output.json",
]
base_args_constraint_checker = [
    "main.py",
    "--import_path",
    "examples/inputs/example_input_constraint_checker_4.json",
    "--export_path",
    "examples/outputs/example_output_constraint_checker.json",
]


def test_valid_command_line_arguments():
    for solver_argument in [["-b"], ["-m"], ["-hb", "10"], ["-g", "100", "100"]]:
        if solver_argument[0] == "-hb":
            sys.argv = [
                "main.py",
                "--import_path",
                "examples/inputs/example_input_normal_8.json",
                "--export_path",
                "examples/outputs/test_output.json",
            ] + solver_argument
        else:
            sys.argv = base_args + solver_argument
        assert main.main()


def test_invalid_command_line_arguments():
    for solver_argument in [["-b 10"], ["-m hello"], ["-hb", "-5"], ["-g", "-100"]]:
        sys.argv = base_args + solver_argument
        with pytest.raises(SystemExit):
            main.main()


def test_invalid_path():
    sys.argv = copy.deepcopy(base_args)
    sys.argv[2] = ""
    with pytest.raises(SystemExit):
        main.main()


def test_output_file_updates():
    sys.argv = base_args + ["-b"]
    checksum = None
    with open("examples/outputs/test_output.json", "rb") as output_file:
        checksum = hashlib.md5(output_file.read()).hexdigest()
    main.main()

    with open("examples/outputs/test_output.json", "rb") as output_file:
        assert checksum != hashlib.md5(output_file.read()).hexdigest()


def test_output_file_validates_against_schema():
    sys.argv = base_args + ["-b"]
    main.main()
    with open("examples/outputs/test_output.json", "r") as output_file:
        with open("schemata/output_schema.json", "r") as schemaFile:
            output_json: dict = json.load(output_file)
            schema = json.load(schemaFile)

            try:
                validate(instance=output_json, schema=schema)
                assert True
            except (ValidationError, SchemaError) as e:
                assert False


def test_possible_constraint_checker():
    sys.argv = base_args_constraint_checker + ["-c", "10"]
    assert main.main()


def test_impossible_constraint_checker():
    sys.argv = base_args_constraint_checker + ["-c", "1"]
    with pytest.raises(SystemExit):
        main.main()


def test_invalid_constraint_checker_arguments():
    sys.argv = base_args_constraint_checker + ["-c"]
    with pytest.raises(SystemExit):
        main.main()


def test_ac3_algorithm():
    sys.argv = base_args + ["-b", "-forward_check"]
    assert main.main()

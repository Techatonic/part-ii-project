import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError

from src.helper.handle_error import handle_error


def read_and_validate_input(path: str, schema_path: str) -> dict:
    with open(path, 'r') as input_file:
        with open(schema_path, 'r') as schemaFile:
            input_json: dict = json.load(input_file)
            schema = json.load(schemaFile)

            try:
                validate(instance=input_json, schema=schema)
            except (ValidationError, SchemaError) as e:
                print(e)
                handle_error("JSON Input is Invalid")

            return input_json

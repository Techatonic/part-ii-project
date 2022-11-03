import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError, SchemaError


def read_input(path):
    with open(path, 'r') as input_file:
        with open('src/input_handling/input_schema.json', 'r') as schemaFile:
            input_json = json.load(input_file)
            schema = json.load(schemaFile)

            try:
                validate(instance=input_json, schema=schema)
            except (ValidationError, SchemaError):
                print("JSON Input is Invalid.")
                exit()

            return input_json

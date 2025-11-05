import json
from pathlib import Path
from jsonschema import validate

def test_directory_rows_schema():
    data = json.loads(Path("data/latest/directory_rows.json").read_text())
    schema = json.loads(Path("schemas/directory_row.schema.json").read_text())
    assert isinstance(data, list) and len(data) > 0, "No rows parsed"
    for row in data:
        validate(row, schema)

import json
import pathlib


def get_fixtures_data():
    file = pathlib.Path(__file__).parent / "fixtures.json"
    with open(file) as f:
        return json.loads(f.read())

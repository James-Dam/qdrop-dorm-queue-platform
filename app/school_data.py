import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "schools.json"

with open(DATA_FILE, encoding="utf-8") as data_file:
    _SCHOOL_DATA = json.load(data_file)


def get_school_choices():
    return [(item["name"], item["name"]) for item in _SCHOOL_DATA.get("schools", [])]


def get_dorm_choices(school_name):
    for item in _SCHOOL_DATA.get("schools", []):
        if item["name"] == school_name:
            return [(dorm, dorm) for dorm in item.get("dorms", [])]
    return []


def get_default_school():
    schools = get_school_choices()
    return schools[0][0] if schools else ""

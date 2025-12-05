import json
from pathlib import Path
from core import config

def load_test_scenarios() -> list[dict]:

    # load scenarios from data\test_scenarios.json using the config getter
    scenarios_path = Path(config.get_test_data_path())
    if not scenarios_path.exists():
        raise FileNotFoundError(f"test scenarios file is missing: {scenarios_path}")
    with open(scenarios_path, encoding="utf-8") as file:
        data = json.load(file)
    # Ensure the result is a list of dictionaries
    if not isinstance(data, list):
        raise ValueError("test scenarios file must contain a list of scenarios")
    return data

def load_user_credentials():

    # load user credentials from data\users.json using the config getter
    users_file = Path(config.get_users_data_path())
    if not users_file.exists():
        raise FileNotFoundError(f"users file is missing:  {users_file}")
    with open(users_file, encoding="utf-8") as file:
        all_users = json.load(file)
    return all_users
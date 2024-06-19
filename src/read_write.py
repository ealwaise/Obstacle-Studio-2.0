import os
import json
from configparser import ConfigParser

def get_value(section: str, key: str) -> str:
    """Gets the value from the input key and section in config.ini."""
    config = ConfigParser()
    config.read("config.ini")
    return config.get(section, key)

def get_path(key: str) -> str:
    """Gets a file path corresponding to the input key."""
    dirs = [os.getcwd()] + get_value("PATHS", key).split(",")
    return os.path.join(*dirs)

def write_setting(key: str, value: bool | int | str) -> None:
    """Writes a user setting to settings.json when a setting is changed.

    key is the key in the json dictionary to be modified.
    value is the new value of the key.
    """
    path = get_path("Settings")
    with open(path, 'r') as file:
        settings = json.load(file)
    settings[key] = value
    with open(path, 'w') as file:
        json.dump(settings, file, indent=4)

def read_setting(key: str) -> bool | int | str:
    """Reads the value corresponding to the input key in settings.json."""
    path = get_path("Settings")
    with open(path, 'r') as file:
        settings = json.load(file)
    return settings[key]
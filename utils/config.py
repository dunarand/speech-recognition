"""
Includes functions for loading various options from the config.json file

functions:
    load_duration

"""

from os import getcwd, path
from json import load

CWD = getcwd()

def load_duration() -> int:
    """Loads the duration setting for speech_recognition.Recognize class to use
    in the adjust_for_ambient_noise method

    Returns:
        int: Integer value of sr_mic Duration keyword in the config.json file
    """
    with open(path.join(CWD, 'config.json'), 'r', encoding = 'utf-8') as f:
        return int(load(f)['sr_mic Duration'])

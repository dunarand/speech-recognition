import os
import json

CWD = os.getcwd()

def load_duration() -> str:
    with open(os.path.join(CWD, 'config.json'), 'r', encoding = 'utf-8') as f:
        return json.load(f)['sr_mic Duration']

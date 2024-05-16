"""Includes a function to install dependencies upon first use

functions:
    install_requirements
"""

from os import path, system, getcwd

CWD = getcwd()

def install_requirements():
    """Installs requirements specified in the requirements.txt file."""
    _path = path.join(CWD, 'requirements.txt')
    system(f'pip install -r {_path}')

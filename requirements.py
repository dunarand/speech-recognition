"""Includes a function to install dependencies upon first use

functions:
    install_requirements
"""

from os import path, system, getcwd

PATH = path.join(getcwd(), 'requirements.txt')

def install_requirements() -> None:
    """Installs dependencies specified in the requirements.txt file."""
    system(f'pip install -r {PATH}')

def update_requirements() -> None:
    """Updates dependencies specified in the requirements.txt file."""
    system(f'pur -r {PATH}')

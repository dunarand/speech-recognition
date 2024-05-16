import os

CWD = os.getcwd()

def install_requirements():
    path = os.path.join(CWD, 'requirements.txt')
    os.system(f'pip install -r {path}')

if __name__ == '__main__':
    install_requirements()

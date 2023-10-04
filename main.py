
from utils import *

dir_path = "output"

if __name__ == "__main__":
    generate(dir_path)
    gcc_compile(dir_path)
    for i in range(1000):
        mutate(dir_path)
        gcc_recompile(dir_path)
        differential_test(dir_path)


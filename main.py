from utils import *

dir_path = "output"
MUTATE_NUMBER = 10000
if __name__ == "__main__":
    init(dir_path)
    for i in range(MUTATE_NUMBER):
        mutate()
        gcc_recompile()
        differential_test()

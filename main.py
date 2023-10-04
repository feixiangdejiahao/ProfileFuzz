from utils import *

dir_path = "output"

if __name__ == "__main__":
    init(dir_path)
    for i in range(1000):
        mutate()
        gcc_recompile()
        differential_test()

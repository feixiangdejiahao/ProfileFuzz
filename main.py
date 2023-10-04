from utils import *

dir_path = "output"

if __name__ == "__main__":
    generate(dir_path)
    gcc_compile()
    for i in range(1000):
        mutate()
        gcc_recompile()
        differential_test()


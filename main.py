from utils import *

dir_path = "output"
MUTATE_NUMBER = 100
if __name__ == "__main__":
    gcda_list = init(dir_path)
    for i in range(MUTATE_NUMBER):
        mutate(gcda_list)
        gcc_recompile(gcda_list)
        differential_test(gcda_list)

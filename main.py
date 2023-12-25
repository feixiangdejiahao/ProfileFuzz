import sys

from GcdaInfo import GCovDataFunctionAnnouncementRecord
from utils import *


def main():
    if len(sys.argv) != 5:
        print("Usage: python3 main.py <dir_path> <file_name> <mutation_number> <generator>")
    dir_path = sys.argv[1]
    file_name = sys.argv[2]
    mutation_number = int(sys.argv[3])
    generator = sys.argv[4]
    if generator == "csmith":
        gcda = init_csmith(dir_path, file_name)
        for i in range(mutation_number):
            constraint = gcda_mutate(gcda)
            gcc_recompile_csmith(gcda)
            differential_test(gcda)
            constraint.constraint_pool.schedule(gcda)
    elif generator == "yarpgen":
        gcda_driver, gcda_func = init_yarpgen(dir_path, file_name)
        for i in range(mutation_number):
            constraint_driver = gcda_mutate(gcda_driver)
            constraint_func = gcda_mutate(gcda_func)
            gcc_recompile_yarpgen(gcda_driver)
            differential_test(gcda_driver)
            constraint_driver.constraint_pool.schedule(gcda_driver)
            constraint_func.constraint_pool.schedule(gcda_func)
    else:
        print("Generator must be csmith or yarpgen")
        exit(-1)


if __name__ == "__main__":
    main()

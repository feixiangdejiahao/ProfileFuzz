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
        gcda, method_constraint_dict, method_block_dict = init_csmith(dir_path, file_name)

        function_index = [gcda.records.index(record) for record in gcda.records if
                          isinstance(record, GCovDataFunctionAnnouncementRecord)]
        for i in range(mutation_number):
            gcda_mutate(gcda, method_constraint_dict, method_block_dict, function_index)
            gcc_recompile_csmith(gcda)
            differential_test(gcda)

    elif generator == "yarpgen":
        gcda_driver, gcda_func, method_constraint_dict_driver, method_block_dict_driver, method_constraint_dict_func, method_block_dict_func = init_yarpgen(
            dir_path, file_name)
        function_index_driver = [gcda_driver.records.index(record) for record in gcda_driver.records if
                                 isinstance(record, GCovDataFunctionAnnouncementRecord)]
        function_index_func = [gcda_func.records.index(record) for record in gcda_func.records if
                               isinstance(record, GCovDataFunctionAnnouncementRecord)]
        for i in range(mutation_number):
            gcda_mutate(gcda_driver, method_constraint_dict_driver, method_block_dict_driver, function_index_driver)
            gcda_mutate(gcda_func, method_constraint_dict_func, method_block_dict_func, function_index_func)
            gcc_recompile_yarpgen(gcda_driver)
            differential_test(gcda_driver)
    else:
        print("Generator must be csmith or yarpgen")
        exit(-1)


def select_method_by_block(method_block_dict):
    sum_up = sum(method_block_dict.values())
    random_number = random.randint(0, sum_up)
    for method in method_block_dict:
        if random_number <= method_block_dict[method]:
            return method
        else:
            random_number -= method_block_dict[method]


if __name__ == "__main__":
    main()

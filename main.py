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
            method_indent_driver = select_method_by_block(method_block_dict)
            index = 0
            for index in function_index:
                if gcda.records[index].ident == method_indent_driver:
                    break
            constraints = method_constraint_dict[method_indent_driver]
            record = gcda.records[index + 1]
            mutate(constraints, record)
            gcc_recompile_csmith(gcda)
            differential_test(gcda)
            print(file_name + "'s mutation " + str(i) + " finished")
            # calculate_similarity(file_name, i)
    elif generator == "yarpgen":
        gcda_driver, gcda_func, method_constraint_dict_driver, method_block_dict_driver, method_constraint_dict_func, method_block_dict_func = init_yarpgen(
            dir_path, file_name)
        function_index_driver = [gcda_driver.records.index(record) for record in gcda_driver.records if
                                 isinstance(record, GCovDataFunctionAnnouncementRecord)]
        function_index_func = [gcda_func.records.index(record) for record in gcda_func.records if
                               isinstance(record, GCovDataFunctionAnnouncementRecord)]
        for i in range(mutation_number):
            method_indent_driver = select_method_by_block(method_block_dict_driver)
            index = 0
            for index in function_index_driver:
                if gcda_driver.records[index].ident == method_indent_driver:
                    break
            constraints = method_constraint_dict_driver[method_indent_driver]
            record = gcda_driver.records[index + 1]
            mutate(constraints, record)
            constraints =list(method_constraint_dict_func.values())[0]
            record = gcda_func.records[function_index_func[0] + 1]
            mutate(constraints, record)
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

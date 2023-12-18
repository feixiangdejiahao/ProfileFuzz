import sys

from GcdaInfo import GCovDataFunctionAnnouncementRecord
from utils import *


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 main.py <dir_path> <file_name> <mutation_number>")
    dir_path = sys.argv[1]
    file_name = sys.argv[2]
    mutation_number = int(sys.argv[3])
    gcda, method_constraint_dict, method_block_dict = init(dir_path, file_name)
    mutation_number = min(mutation_number, len(method_constraint_dict))
    function_index = [gcda.records.index(record) for record in gcda.records if
                      isinstance(record, GCovDataFunctionAnnouncementRecord)]
    for i in range(mutation_number):
        method_indent = select_method_by_block(method_block_dict)
        index = 0
        for index in function_index:
            if gcda.records[index].ident == method_indent:
                break
        constraints = method_constraint_dict[method_indent]
        record = gcda.records[index + 1]
        mutate(constraints, record)
        gcc_recompile(gcda)
        differential_test(gcda)
        print(file_name + "'s mutation " + str(i) + " finished")
        # calculate_similarity(file_name, i)


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

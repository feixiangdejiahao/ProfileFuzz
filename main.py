import sys

from utils import *

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 main.py <dir_path> <file_name> <mutation_number>")
    dir_path = sys.argv[1]
    file_name = sys.argv[2]
    mutation_number = int(sys.argv[3])
    gcda, method_constraint_dict = init(dir_path, file_name)
    for i in range(mutation_number):
        mutate(gcda, method_constraint_dict)
        gcc_recompile(gcda)
        differential_test(gcda)
        print(file_name + "'s mutation " + str(i) + " finished")
        # calculate_similarity(file_name, i)

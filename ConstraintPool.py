import os
import re


def calculate_similarity(gcda):
    file_name = gcda.target_binary_name
    cmd = "radiff2 -s " + file_name + "_O3 " + file_name + "_mut_O3"
    result = os.popen(cmd).read()
    pattern = r"similarity:\s([0-9.]+)"
    match = re.search(pattern, result)
    sim = match.group(1)
    return float(sim)


class ConstraintPool:
    def __init__(self, ):
        self.constraint = None
        self.constraint_pool = []
        self.similarity_list = []

    def record(self, constraint):
        self.constraint = constraint

    def add(self):
        self.constraint_pool.append(self.constraint)

    def get(self):
        return self.constraint_pool

    def get_constraint(self):
        return self.constraint

    def schedule(self, gcda):
        sim = calculate_similarity(gcda)
        print("similarity: " + str(sim))
        if sim not in self.similarity_list and sim != 1.0:
            print("new similarity: " + str(sim))
            self.similarity_list.append(sim)
            self.constraint_pool.append(self.constraint)
            print("constraint pool: " + str(self.constraint_pool))
        else:
            print("no new similarity found")

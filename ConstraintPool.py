from utils import calculate_similarity


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
        if sim in self.similarity_list:
            return
        else:
            self.similarity_list.append(sim)
            self.constraint_pool.append(self.constraint)

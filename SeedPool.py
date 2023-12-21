from utils import calculate_similarity


class SeedPool:
    def __init__(self, seed):
        self.seed = seed
        self.pool = []
        self.similarity_list = []
        self.pool.append(seed)

    def add(self, seed):
        self.pool.append(seed)

    def get(self):
        return self.pool

    def getSeed(self):
        return self.seed

    def schedule(self, gcda):
        calculate_similarity(gcda)

    def __str__(self):
        return str(self.seed) + " " + str(self.pool)

import random

from ConstraintPool import ConstraintPool
from GcnoInfo import GcovNoteArcSetRecord, GcovNoteLineSetRecord
from z3 import *


class GcovConstraint:
    def __init__(self, ident, records):
        self.ident = ident
        self.records = records
        self.arc_list = []
        self.counter_list = []
        self.block_list = []
        self.constraints = []
        self.constraint_pool = ConstraintPool()

    def extract_arc_list(self):  # extract all arcs with counter from gcno
        for record in self.records:
            if isinstance(record, GcovNoteArcSetRecord):
                for arc in record.arcs:
                    if arc.flag != 3:
                        self.arc_list.append(arc)
                        if arc.flag == 0 or arc.flag == 4:
                            self.counter_list.append(arc)

    def extract_block_list(self):  # extract all blocks with line number from gcno
        for record in self.records:
            if isinstance(record, GcovNoteLineSetRecord):
                self.block_list.append(record.block_number)

    def construct_constraint(self):
        self.extract_block_list()
        self.extract_arc_list()
        for block in self.block_list:
            outgoing_arc = []
            incoming_arc = []
            for arc in self.arc_list:
                if arc.source_block_number == block:
                    outgoing_arc.append(arc)
                elif arc.destination_block_number == block:
                    incoming_arc.append(arc)
            if len(outgoing_arc) == 0 or len(incoming_arc) == 0:
                continue
            constraint = Constraint(incoming_arc, outgoing_arc)
            self.constraints.append(constraint)

    def solve(self, index, value):
        solver = Solver()
        for arc in self.arc_list:
            solver.add(Int("arc" + str(arc.source_block_number) + "_" + str(arc.destination_block_number)) >= 0)
        for constraint in self.constraints:
            incoming_arc = constraint.incoming_edge
            outgoing_arc = constraint.outgoing_edge
            incoming_sum, outgoing_sum = 0, 0
            for arc in incoming_arc:
                incoming_sum += Int("arc" + str(arc.source_block_number) + "_" + str(arc.destination_block_number))
            for arc in outgoing_arc:
                outgoing_sum += Int("arc" + str(arc.source_block_number) + "_" + str(arc.destination_block_number))
            solver.add(incoming_sum == outgoing_sum)
        assign_constraint = Int("arc" + str(self.counter_list[index].source_block_number) + "_" + str(
            self.counter_list[index].destination_block_number)) == value
        solver.add(assign_constraint)
        for c in self.constraint_pool.get():
            solver.add(c)
        self.constraint_pool.record(assign_constraint)
        solutions = []
        while solver.check() == sat:
            if len(solutions) > 1000:
                break
            model = solver.model()
            solution = []
            for counter in self.counter_list:
                solution.append(
                    model[Int("arc" + str(counter.source_block_number) + "_" + str(
                        counter.destination_block_number))].as_long())
            solutions.append(solution)
            block = []
            for d in model:
                c = d()
                block.append(c != model[d])
            solver.add(And(block))
        if not solutions:
            return False
        return random.choice(solutions)


class Constraint:
    def __init__(self, incoming_edge, outgoing_edge):
        self.incoming_edge = incoming_edge
        self.outgoing_edge = outgoing_edge

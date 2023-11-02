from GcnoInfo import GcovNoteArcSetRecord, GcovNoteLineSetRecord


class GcovConstraint:
    def __init__(self, ident, records):
        self.ident = ident
        self.records = records
        self.arc_list = []
        self.block_list = []
        self.constraint = []

    def extract_arc_list(self):  # extract all arcs with counter from gcno
        for record in self.records:
            if isinstance(record, GcovNoteArcSetRecord):
                for arc in record.arcs:
                    self.arc_list.append(arc)

    def extract_line_list(self):  # extract all blocks with line number from gcno
        for record in self.records:
            if isinstance(record, GcovNoteLineSetRecord):
                self.block_list.append(record.block_number)

    def construct_constraint(self):
        outgoing_arc_list = []
        incoming_arc_list = []
        for block in self.block_list:
            outgoing_arc = []
            incoming_arc = []
            for arc in self.arc_list:
                if arc.source_block_number == block:
                    outgoing_arc.append(arc)
                if arc.destination_block_number == block:
                    incoming_arc.append(arc)
            outgoing_arc_list.append(outgoing_arc)
            incoming_arc_list.append(incoming_arc)
        for i in range(len(self.block_list)):
            outgoing_arc = outgoing_arc_list[i]
            incoming_arc = incoming_arc_list[i]
            if len(outgoing_arc) == 0 or len(incoming_arc) == 0:
                continue
            if not all(arc.flag == 0 or arc.flag == 4 for arc in outgoing_arc):
                continue
            if not all(arc.flag == 0 or arc.flag == 4 for arc in incoming_arc):
                continue
            constraint = Constraint([self.arc_list.index(i) for i in incoming_arc],
                                    [self.arc_list.index(i) for i in outgoing_arc])
            self.constraint.append(constraint)


class Constraint:
    def __init__(self, incoming_counter, outgoing_counter):
        self.incoming_counter = incoming_counter
        self.outgoing_counter = outgoing_counter

    def contain_target_counter(self, counter_index):
        return counter_index in self.incoming_counter or counter_index in self.outgoing_counter

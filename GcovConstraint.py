from GcnoInfo import GcovNoteArcSetRecord, GcovNoteLineSetRecord


class GcovConstraint:
    def __init__(self, ident, records):
        self.ident = ident
        self.records = records
        self.arc_list = []
        self.block_list = []
        self.constraints = []

    def extract_arc_list(self):  # extract all arcs with counter from gcno
        for record in self.records:
            if isinstance(record, GcovNoteArcSetRecord):
                for arc in record.arcs:
                    if arc.flag == 0 or arc.flag == 4:
                        self.arc_list.append(arc)

    def extract_block_list(self):  # extract all blocks with line number from gcno
        for record in self.records:
            if isinstance(record, GcovNoteLineSetRecord):
                self.block_list.append(record.block_number)

    def construct_constraint(self):
        self.extract_arc_list()
        self.extract_block_list()
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
            constraint = Constraint([self.arc_list.index(i) for i in incoming_arc],
                                    [self.arc_list.index(i) for i in outgoing_arc],
                                    all(i in self.arc_list for i in incoming_arc),
                                    all(i in self.arc_list for i in incoming_arc))
            self.constraints.append(constraint)


class Constraint:
    def __init__(self, incoming_counter, outgoing_counter, incoming_status, outgoing_status):
        self.incoming_counters = incoming_counter
        self.outgoing_counters = outgoing_counter
        self.incoming_status = incoming_status  # incoming_status = True means all incoming arcs are counter
        self.outgoing_status = outgoing_status  # outgoing_status = True means all outgoing arcs are counter

    def incoming_contain_target_counter(self, counter_index):
        return counter_index in self.incoming_counters

    def outgoing_contain_target_counter(self, counter_index):
        return counter_index in self.outgoing_counters

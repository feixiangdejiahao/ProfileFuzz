import os
import random
import sys

import utils
from GcdaInfo import GcdaInfo, GCovDataFunctionAnnouncementRecord
from GcnoInfo import GcnoInfo


def modify_gcda(gcda_name, index, counter):  # index: the index of the function in gcda file
    gcda = GcdaInfo()
    gcda.load(gcda_name)
    gcda.pull_records()
    records = gcda.records
    function_index = [records.index(record) for record in records if
                      isinstance(record, GCovDataFunctionAnnouncementRecord)]
    function_index = function_index[index]
    records[function_index + 1].counters = counter
    gcda.save(gcda_name)


if len(sys.argv) != 4:
    print("Usage: python3 debug.py <gcda_name> <index> <counter>")
gcda_name = sys.argv[1]
index = int(sys.argv[2])
counter = eval(sys.argv[3])
modify_gcda(gcda_name, index, counter)

import os
import random

from GcdaInfo import GcdaInfo, GCovDataFunctionAnnouncementRecord

gcda = GcdaInfo()
gcda.load("output/test1/test1.gcda")
gcda.pull_records()
records = gcda.records
function_index = [records.index(record) for record in records if
                  isinstance(record, GCovDataFunctionAnnouncementRecord)]
index = random.choice(function_index)
function = records[index]
counters = records[index + 1]

i = 0
while i <= 10:
    gcda.extremum_mutation(counters)
    gcda.one_value_mutation(counters)
    i += 1
gcda.save("output/test1/test1_mut-test1.gcda")
a = 1

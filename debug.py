import os

from GcnoInfo import GcnoInfo

gcno = GcnoInfo()
gcno.load("tmp/test.gcno")
gcno.pull_records()
a = 1

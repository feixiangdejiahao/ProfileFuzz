import os
import random
import shutil

from GcdaInfo import GcdaInfo, GCovDataCounterBaseRecord
from GcnoInfo import GcnoInfo, GcovNoteFunctionAnnouncementRecord
from GcovConstraint import GcovConstraint


def construct_constraint(gcno):
    records = gcno.records
    function_announce_record_index = [records.index(record) for record in records if
                                      isinstance(record, GcovNoteFunctionAnnouncementRecord)]
    function_announce_record_index.append(len(records))
    method_constraint_dict = {}
    for i in range(len(function_announce_record_index) - 1):
        ident = records[function_announce_record_index[i]].ident
        method_constraint_dict[ident] = GcovConstraint(ident, records[function_announce_record_index[i] + 2:
                                                                      function_announce_record_index[i + 1]])
        method_constraint_dict[ident].construct_constraint()
    return method_constraint_dict


def construct_block(gcno):
    records = gcno.records
    function_announce_record_index = [records.index(record) for record in records if
                                      isinstance(record, GcovNoteFunctionAnnouncementRecord)]
    method_block_dict = {}
    for i in range(len(function_announce_record_index)):
        ident = records[function_announce_record_index[i]].ident
        method_block_dict[ident] = records[function_announce_record_index[i] + 1].block_count
    return method_block_dict


def get_basic_info(file_name):
    gcno = GcnoInfo()
    gcno.load(file_name + ".gcno")
    gcno.pull_records()
    method_constraint_dict = construct_constraint(gcno)
    method_block_dict = construct_block(gcno)
    return method_constraint_dict, method_block_dict


def init(dir_path, file_name):
    file_name = "test" + file_name
    if os.path.exists(dir_path + file_name):
        shutil.rmtree(dir_path + file_name)
    os.makedirs(dir_path + file_name)
    os.chdir(dir_path + file_name)
    gcda = generate_compile(file_name)
    method_constraint_dict, method_block_dict = get_basic_info(file_name)
    return gcda, method_constraint_dict, method_block_dict


def generate_compile(file_name):
    generate_cmd = "csmith > " + file_name + ".c"
    compile_cmd = "gcc -w --coverage " + file_name + ".c -o " + file_name
    execute_cmd = "timeout 30s ./" + file_name
    result = 1
    while result != 0:
        os.system(generate_cmd)
        os.system(compile_cmd)
        result = os.system(execute_cmd)
    cmd = "./" + file_name + " > " + file_name + ".txt"
    os.system(cmd)
    shutil.copyfile(file_name + ".gcda", file_name + "_mut-" + file_name + ".gcda")
    gcda = GcdaInfo()
    gcda.load(file_name + "_mut-" + file_name + ".gcda")
    gcda.pull_records()
    return gcda


def gcc_recompile(gcda):
    cmd = "gcc -w -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut.txt"
    os.system(cmd)
    cmd = "gcc -w -O1 -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_O1.txt"
    os.system(cmd)
    cmd = "gcc -w -O2 -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_O2.txt"
    os.system(cmd)
    cmd = "gcc -w -O3 -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_O3.txt"
    os.system(cmd)
    cmd = "gcc -w -Og -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_Og.txt"
    os.system(cmd)
    cmd = "gcc -w -Os -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_Os.txt"
    os.system(cmd)
    cmd = "gcc -w -Ofast -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_Ofast.txt"
    os.system(cmd)
    cmd = "gcc -w -Oz -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_Oz.txt"
    os.system(cmd)
    cmd = "clang -w " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    os.system(cmd)
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut_clang.txt"
    os.system(cmd)


def differential_test(gcda):
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut.txt"
    result = os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_O1.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_O2.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_O3.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_Og.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_Os.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_Ofast.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_Oz.txt"
    result += os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut_clang.txt"
    result += os.system(cmd)
    if result != 0:
        print("bug found in " + gcda.source_file_name)
        save_bug_report(gcda.source_file_name)
        # write to bug_report.txt


def calculate_similarity(file_name, i):
    cmd = "echo \"\n=== iteration " + str(i) + " ===\n\" >> similarity.txt"
    os.system(cmd)
    cmd = "radiff2 -s " + file_name + " " + file_name + "_mut >> similarity.txt"
    os.system(cmd)


def mutate(constraints, record):
    while True:
        if isinstance(record, GCovDataCounterBaseRecord):
            index = random.randint(0, len(record.counters) - 1)
            counter = record.counters[index]
            if counter >= 0:
                value = 0
            else:
                value = random.randint(0, 2 ** 32 - 1)
            result = constraints.solve(index, value)
            if isinstance(result, list):
                record.counters = result
                break


def save_bug_report(file_name):
    os.makedirs("../bug_report/" + file_name)
    # copy source code
    shutil.copyfile(file_name + ".c", "../bug_report/" + file_name + "/" + file_name + ".c")
    # copy result
    shutil.copyfile(file_name + ".txt", "../bug_report/" + file_name + "/" + file_name + ".txt")
    shutil.copyfile(file_name + "_mut.txt",
                    "../bug_report/" + file_name + "/" + file_name + "_mut.txt")
    # copy gcda file
    shutil.copyfile(file_name + "_mut-" + file_name + ".gcda",
                    "../bug_report/" + file_name + "/" + file_name + "_mut-" + file_name + ".gcda")
    # copy executable file
    shutil.copyfile(file_name + "_mut", "../bug_report/" + file_name + "/" + file_name + "_mut")
    shutil.copyfile(file_name, "../bug_report/" + file_name + "/" + file_name)

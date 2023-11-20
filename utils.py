import os
import shutil

from GcdaInfo import GcdaInfo
from GcnoInfo import GcnoInfo, GcovNoteFunctionAnnouncementRecord
from GcovConstraint import GcovConstraint


def construct(gcno):
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


def build_constraint(file_name):
    gcno = GcnoInfo()
    gcno.load(file_name + ".gcno")
    gcno.pull_records()
    method_constraint_dict = construct(gcno)
    return method_constraint_dict


def init(dir_path, file_name):
    file_name = "test" + file_name
    # os.makedirs(dir_path + "/" + file_name)
    os.chdir(dir_path + "/" + file_name)
    gcda = generate_compile(file_name)
    method_constraint_dict = build_constraint(file_name)
    return gcda, method_constraint_dict


def generate_compile(file_name):
    generate_cmd = "csmith > " + file_name + ".c"
    compile_cmd = "gcc -fprofile-generate " + file_name + ".c -o " + file_name
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
    cmd = "gcc -fprofile-use " + gcda.source_file_name + ".c -o " + gcda.source_file_name + "_mut"
    result = os.system(cmd)
    while result != 0:
        init_gcda = GcdaInfo()
        init_gcda.load(gcda.source_file_name + ".gcda")
        init_gcda.pull_records()
        mutate(init_gcda)
        init_gcda.save(gcda.source_file_name + "_mut-" + gcda.source_file_name + ".gcda")
        result = os.system(cmd)


def differential_test(gcda):
    cmd = "./" + gcda.source_file_name + "_mut > " + gcda.source_file_name + "_mut.txt"
    os.system(cmd)
    cmd = "diff " + gcda.source_file_name + ".txt " + gcda.source_file_name + "_mut.txt"
    result = os.system(cmd)
    if result != 0:
        print("bug found in " + gcda.source_file_name)
        save_bug_report(gcda.source_file_name)
        # write to bug_report.txt


def mutate(gcda, method_constraint_dict):
    gcda.mutate(method_constraint_dict)
    gcda.save()


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

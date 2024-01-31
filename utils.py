import os
import random
import shutil
import subprocess
import time

from GcdaInfo import GcdaInfo, GCovDataCounterBaseRecord, GCovDataFunctionAnnouncementRecord
from GcnoInfo import GcnoInfo, GcovNoteFunctionAnnouncementRecord
from GcovConstraint import GcovConstraint


def select_method_by_block(method_block_dict):
    sum_up = sum(method_block_dict.values())
    random_number = random.randint(0, sum_up)
    for method in method_block_dict:
        if random_number <= method_block_dict[method]:
            return method
        else:
            random_number -= method_block_dict[method]


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


def get_basic_info_csmith(file_name):
    gcno = GcnoInfo()
    gcno.load(file_name + ".gcno")
    gcno.pull_records()
    method_constraint_dict = construct_constraint(gcno)
    method_block_dict = construct_block(gcno)
    return method_constraint_dict, method_block_dict


def init_csmith(dir_path, file_name, optimization_level):
    file_name = "test" + file_name + "/" + optimization_level
    if os.path.exists(dir_path + file_name):
        shutil.rmtree(dir_path + file_name)
    os.makedirs(dir_path + file_name)
    os.chdir(dir_path + file_name)
    gcda = generate_compile_csmith(file_name, optimization_level)
    gcda.method_constraint_dict, gcda.method_block_dict = get_basic_info_csmith(file_name)
    gcda.function_index = [gcda.records.index(record) for record in gcda.records if
                           isinstance(record, GCovDataFunctionAnnouncementRecord)]
    return gcda


def get_basic_info_yarpgen(file_name):
    gcno_driver = GcnoInfo()
    gcno_driver.load(file_name + "-driver.gcno")
    gcno_driver.pull_records()
    gcno_func = GcnoInfo()
    gcno_func.load(file_name + "-func.gcno")
    gcno_func.pull_records()
    method_constraint_dict_driver = construct_constraint(gcno_driver)
    method_block_dict_driver = construct_block(gcno_driver)
    method_constraint_dict_func = construct_constraint(gcno_func)
    method_block_dict_func = construct_block(gcno_func)
    return method_constraint_dict_driver, method_block_dict_driver, method_constraint_dict_func, method_block_dict_func


def init_yarpgen(dir_path, file_name, optimization_level):
    file_name = "test" + file_name
    if os.path.exists(dir_path + file_name):
        shutil.rmtree(dir_path + file_name)
    os.makedirs(dir_path + file_name)
    os.chdir(dir_path + file_name)
    gcda_driver, gcda_func = generate_compile_yarpgen(file_name, optimization_level)
    method_constraint_dict_driver, method_block_dict_driver, method_constraint_dict_func, method_block_dict_func = get_basic_info_yarpgen(
        file_name)
    gcda_driver.method_constraint_dict = method_constraint_dict_driver
    gcda_driver.method_block_dict = method_block_dict_driver
    gcda_func.method_constraint_dict = method_constraint_dict_func
    gcda_func.method_block_dict = method_block_dict_func
    gcda_driver.function_index = [gcda_driver.records.index(record) for record in gcda_driver.records if
                                  isinstance(record, GCovDataFunctionAnnouncementRecord)]
    gcda_func.function_index = [gcda_func.records.index(record) for record in gcda_func.records if
                                isinstance(record, GCovDataFunctionAnnouncementRecord)]
    return gcda_driver, gcda_func


def generate_compile_yarpgen(file_name, optimization_level):
    generate_cmd = "yarpgen --std=c"
    compile_cmd = "gcc -w driver.c func.c -o " + file_name
    execute_cmd = "timeout 30s ./" + file_name + " > " + file_name + ".txt 2>&1"
    while True:
        result = execute_command(generate_cmd)
        result += execute_command(compile_cmd)
        result += execute_command(execute_cmd)
        if result == 0:
            break
    # PGO compilation
    cmd = "gcc -w --coverage driver.c func.c -o " + file_name + " -" + optimization_level
    execute_command(cmd)
    cmd = "./" + file_name
    execute_command(cmd)
    cmd = "gcc -w -fprofile-use driver.c func.c -o " + file_name + " -" + optimization_level
    execute_command(cmd)
    shutil.copyfile(file_name + "-func.gcda", file_name + "_mut-func.gcda")
    shutil.copyfile(file_name + "-driver.gcda", file_name + "_mut-driver.gcda")
    gcda_driver = GcdaInfo()
    gcda_driver.load(file_name + "_mut-driver.gcda")
    gcda_driver.pull_records()
    gcda_func = GcdaInfo()
    gcda_func.load(file_name + "_mut-func.gcda")
    gcda_func.pull_records()
    return gcda_driver, gcda_func


def generate_compile_csmith(file_name, optimization_level):
    generate_cmd = "csmith > " + file_name + ".c"
    compile_cmd = "gcc -w " + file_name + ".c -o " + file_name
    execute_cmd = "timeout 30s ./" + file_name + " > " + file_name + ".txt 2>&1"
    result = 1
    while result != 0:
        execute_command(generate_cmd)
        execute_command(compile_cmd)
        result = execute_command(execute_cmd)

    # PGO compilation
    cmd = "gcc -w --coverage " + file_name + ".c -o " + file_name + " -" + optimization_level
    execute_command(cmd)
    cmd = "./" + file_name
    execute_command(cmd)
    cmd = "gcc -w -fprofile-use " + file_name + ".c -o " + file_name + " -" + optimization_level
    execute_command(cmd)
    # delete_old_gcda(file_name, file_name)
    shutil.copyfile(file_name + ".gcda", file_name + "_mut-" + file_name + ".gcda")
    gcda = GcdaInfo()
    gcda.load(file_name + "_mut-" + file_name + ".gcda")
    gcda.pull_records()
    return gcda


def gcc_recompile_csmith(gcda, optimization_level):
    print("recompiling...")
    base_cmd = ["gcc", "-w", "-fprofile-use"]
    clang_cmd = ["clang", "-w"]
    optimization_level = "-" + optimization_level
    source_file = gcda.target_binary_name + ".c"
    output_base = gcda.target_binary_name + "_mut"
    delete_old_file(gcda.target_binary_name)
    compiled_name = output_base + ".txt"
    cmd = base_cmd + [optimization_level, source_file, "-o", output_base]
    execute_command(" ".join(cmd))
    execute_command(f"./{output_base} > {compiled_name} 2>&1")
    # Clang Compilation
    clang_compiled_name = output_base + "_clang.txt"
    cmd = clang_cmd + [source_file, "-o", output_base]
    execute_command(" ".join(cmd))
    execute_command(f"./{output_base} > {clang_compiled_name} 2>&1")


def differential_test(gcda):
    print("differential testing...")
    target_binary_name = gcda.target_binary_name
    cmd = "diff " + target_binary_name + ".txt " + target_binary_name + "_mut.txt"
    bug_found = execute_command(cmd)
    if not bug_found:
        print(f"No bugs found in {target_binary_name}")
    else:
        print(f"Bug found in {target_binary_name}")
        save_bug_report(target_binary_name, cmd)


def delete_old_file(target_binary_name):
    if os.path.exists(target_binary_name + "_mut"):
        os.remove(target_binary_name + "_mut")
    if os.path.exists(target_binary_name + "_mut.txt"):
        cmd = "rm " + target_binary_name + "_mut.txt"
        execute_command(cmd)


def delete_old_gcda(source_code_name, target_binary_name):
    if os.path.exists(target_binary_name + "_mut-" + source_code_name + ".gcda"):
        os.remove(target_binary_name + "_mut-" + source_code_name + ".gcda")


def gcc_recompile_yarpgen(gcda_driver, optimization_level):
    print("recompiling...")
    base_cmd = ["gcc", "-w", "-fprofile-use"]
    clang_cmd = ["clang", "-w"]
    driver_file = "driver.c"
    func_file = "func.c"
    optimization_level = "-" + optimization_level
    output_base = gcda_driver.target_binary_name + "_mut"
    delete_old_file(gcda_driver.target_binary_name)
    compiled_name = output_base + ".txt"
    cmd = base_cmd + [optimization_level, driver_file, func_file, "-o", output_base]
    execute_command(" ".join(cmd))
    execute_command(f"./{output_base} > {compiled_name} 2>&1")
    # Clang Compilation
    clang_compiled_name = output_base + "_clang.txt"
    cmd = clang_cmd + [driver_file, func_file, "-o", output_base]
    execute_command(" ".join(cmd))
    execute_command(f"./{output_base} > {clang_compiled_name} 2>&1")


def gcda_mutate(gcda):
    print("mutating...")
    while True:
        method_indent_driver = select_method_by_block(gcda.method_block_dict)
        index = 0
        for index in gcda.function_index:
            if gcda.records[index].ident == method_indent_driver:
                break
        constraints = gcda.method_constraint_dict[method_indent_driver]
        record = gcda.records[index + 1]
        if isinstance(record, GCovDataCounterBaseRecord):
            index = random.randint(0, len(record.counters) - 1)
            value = random.randint(0, 2 ** 10 - 1)
            result = constraints.solve(index, value)
            if isinstance(result, list):
                record.counters = result
                break
            elif len(record.counters) == 1:
                break
    gcda.save(gcda.target_binary_name + "_mut-" + gcda.source_file_name + ".gcda")
    return constraints


not_a_bug = ["relink with --no-relax"]


def execute_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0 and not any(x in stderr.decode() for x in not_a_bug):
        print("Error executing command:", command)
        print(stderr.decode())
    if process.returncode != 0:
        save_bug_report("execution_error", command)
        exit(-1)
    return process.returncode


def save_bug_report(file_name, cmd):
    cmd = "echo " + cmd + " > " + "bug_cmd.txt"
    execute_command(cmd)
    time_stamp = str(int(time.time()))
    os.makedirs("../bug_report/" + file_name + "_" + time_stamp, exist_ok=True)
    cmd = "cp * ../bug_report/" + file_name + "_" + time_stamp
    execute_command(cmd)

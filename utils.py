import os
import random
import shutil
import subprocess
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


def get_basic_info_csmith(file_name):
    gcno = GcnoInfo()
    gcno.load(file_name + ".gcno")
    gcno.pull_records()
    method_constraint_dict = construct_constraint(gcno)
    method_block_dict = construct_block(gcno)
    return method_constraint_dict, method_block_dict


def init_csmith(dir_path, file_name):
    file_name = "test" + file_name
    if os.path.exists(dir_path + file_name):
        shutil.rmtree(dir_path + file_name)
    os.makedirs(dir_path + file_name)
    os.chdir(dir_path + file_name)
    gcda = generate_compile_csmith(file_name)
    method_constraint_dict, method_block_dict = get_basic_info_csmith(file_name)
    return gcda, method_constraint_dict, method_block_dict


def generate_compile_yarpgen(file_name):
    generate_cmd = "yarpgen --std=c"
    compile_cmd = "gcc -w -mcmodel=large --coverage driver.c func.c -o " + file_name + "&> /dev/null"
    execute_cmd = "timeout 30s ./" + file_name + "&> /dev/null"
    while True:
        result = os.system(generate_cmd)
        result += os.system(compile_cmd)
        result += os.system(execute_cmd)
        if result == 0:
            break
    cmd = "./" + file_name + " > " + file_name + ".txt"
    os.system(cmd)
    shutil.copyfile(file_name + "-func.gcda", file_name + "_mut-func.gcda")
    shutil.copyfile(file_name + "-driver.gcda", file_name + "_mut-driver.gcda")
    gcda_driver = GcdaInfo()
    gcda_driver.load(file_name + "_mut-driver.gcda")
    gcda_driver.pull_records()
    gcda_func = GcdaInfo()
    gcda_func.load(file_name + "_mut-func.gcda")
    gcda_func.pull_records()
    return gcda_driver, gcda_func


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


def init_yarpgen(dir_path, file_name):
    file_name = "test" + file_name
    if os.path.exists(dir_path + file_name):
        shutil.rmtree(dir_path + file_name)
    os.makedirs(dir_path + file_name)
    os.chdir(dir_path + file_name)
    gcda_driver, gcda_func = generate_compile_yarpgen(file_name)
    method_constraint_dict_driver, method_block_dict_driver, method_constraint_dict_func, method_block_dict_func = get_basic_info_yarpgen(
        file_name)
    return gcda_driver, gcda_func, method_constraint_dict_driver, method_block_dict_driver, method_constraint_dict_func, method_block_dict_func


def generate_compile_csmith(file_name):
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
    cmd = "gcc -w -O3 -fprofile-use " + file_name + ".c -o " + file_name + "_O3"
    os.system(cmd)
    shutil.copyfile(file_name + ".gcda", file_name + "_mut-" + file_name + ".gcda")
    gcda = GcdaInfo()
    gcda.load(file_name + "_mut-" + file_name + ".gcda")
    gcda.pull_records()
    return gcda


def gcc_recompile_csmith(gcda):
    base_cmd = ["gcc", "-w", "-fprofile-use"]
    optimization_levels = ["", "-O1", "-O2", "-O3", "-Og", "-Os", "-Ofast"]
    clang_cmd = ["clang", "-w"]

    source_file = gcda.source_file_name + ".c"
    output_base = gcda.source_file_name + "_mut"

    for opt in optimization_levels:
        compiled_name = output_base + opt.replace("-", "_") + ".txt"
        cmd = base_cmd + [opt, source_file, "-o", output_base]
        execute_command(" ".join(cmd))
        execute_command(f"./{output_base} > {compiled_name}")

    # Clang Compilation
    clang_compiled_name = output_base + "_clang.txt"
    cmd = clang_cmd + [source_file, "-o", output_base]
    execute_command(" ".join(cmd))
    execute_command(f"./{output_base} > {clang_compiled_name}")


def differential_test(gcda):
    optimization_levels = ["", "_O1", "_O2", "_O3", "_Og", "_Os", "_Ofast", "_clang"]
    source_file_base = gcda.source_file_name
    cmd = "diff --from-file " + source_file_base + ".txt "
    for opt in optimization_levels:
        cmd += f"{source_file_base}_mut{opt}.txt "
    bug_found = os.system(cmd)
    if not bug_found:
        print(f"No bugs found in {source_file_base}")
    else:
        print(f"Bug found in {source_file_base}")
        save_bug_report(source_file_base)


def delete_old_file(source_file_name):
    if os.path.exists(source_file_name + "_mut"):
        os.remove(source_file_name + "_mut")
    if os.path.exists(source_file_name + "_mut_O1.txt"):
        cmd = "rm " + source_file_name + "_mut_*.txt"
        os.system(cmd)


def gcc_recompile_yarpgen(gcda_driver):
    base_cmd = ["gcc", "-w", "-fprofile-use", "-mcmodel=large"]
    optimization_levels = ["", "-O1", "-O2", "-O3", "-Og", "-Os", "-Ofast"]
    clang_cmd = ["clang", "-w"]

    driver_file = "driver.c"
    func_file = "func.c"
    output_base = gcda_driver.source_file_name + "_mut"
    delete_old_file(gcda_driver.source_file_name)
    for opt in optimization_levels:
        compiled_name = output_base + opt.replace("-", "_") + ".txt"
        cmd = base_cmd + [opt, driver_file, func_file, "-o", output_base]
        execute_command(" ".join(cmd))
        execute_command(f"./{output_base} > {compiled_name}")

    # Clang Compilation
    clang_compiled_name = output_base + "_clang.txt"
    cmd = clang_cmd + [driver_file, func_file, "-o", output_base]
    execute_command(" ".join(cmd))
    execute_command(f"./{output_base} > {clang_compiled_name}")


def calculate_similarity(gcda):
    file_name = gcda.source_file_name
    cmd = "radiff2 -s " + file_name + "_O3 " + file_name + "_mut_O3"
    sim = os.popen(cmd).read()


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


def execute_command(command):
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print("Error executing command:", command)
        print(stderr)
    return stdout


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

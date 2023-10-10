import os
import shutil
from multiprocessing import Pool

from gcda import GcdaInfo

TEST_NUMBER = 100


def init(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)
    pool = Pool(32)
    gcda_list = []
    for i in range(TEST_NUMBER):
        file_name = "test" + str(i)
        gcda = pool.apply_async(generate_compile, (dir_path, file_name,))
        gcda_list.append(gcda)
        # generate_compile(file_name)
    pool.close()
    pool.join()
    return gcda_list


def generate_compile(dir_path, file_name):
    dir_path = dir_path + "/" + file_name
    os.mkdir(dir_path)
    generate_cmd = "csmith > " + dir_path + "/" + file_name + ".c"
    compile_cmd = "gcc -fprofile-generate " + dir_path + "/" + file_name + ".c -o " + dir_path + "/" + file_name
    execute_cmd = "timeout 30s ./" + dir_path + "/" + file_name
    result = 1
    while result != 0:
        os.system(generate_cmd)
        os.system(compile_cmd)
        result = os.system(execute_cmd)
    cmd = "./" + dir_path + "/" + file_name + " > " + dir_path + "/" + file_name + ".txt"
    os.system(cmd)
    shutil.copyfile(dir_path + "/" + file_name + ".gcda", dir_path + "/" + file_name + "_mut-" + file_name + ".gcda")
    gcda = GcdaInfo()
    gcda.load(dir_path + "/" + file_name + "_mut-" + file_name + ".gcda")
    gcda.pull_records()
    return gcda


def gcc_recompile(gcda_list):
    pool = Pool(32)
    for gcda in gcda_list:
        pool.apply_async(recompile_one_file, (gcda,))
    pool.close()
    pool.join()


def recompile_one_file(gcda):
    cmd = "gcc -fprofile-use " + gcda.file_path + "/" + gcda.source_file_name + ".c -o " + gcda.file_path + "/" + gcda.source_file_name + "_mut"
    result = os.system(cmd)
    while result != 0:
        mutate_single_gcda(gcda)
        result = os.system(cmd)


def differential_test(gcda_list):
    pool = Pool(32)
    for gcda in gcda_list:
        cmd = "./" + gcda.file_path + "/" + gcda.source_file_name + "_mut > " + gcda.file_path + "/" + gcda.source_file_name + "_mut.txt"
        os.system(cmd)
        cmd = "diff " + gcda.file_path + "/" + gcda.source_file_name + ".txt " + gcda.file_path + "/" + gcda.source_file_name + "_mut.txt"
        result = os.system(cmd)
        if result != 0:
            print("bug found in " + gcda.source_file_name)
            os.makedirs("bug_report/" + gcda.source_file_name)
            save_bug_report(gcda.source_file_name)
            # write to bug_report.txt
        os.remove(gcda.file_path + "/" + gcda.source_file_name + "_mut.txt")
    pool.close()
    pool.join()


def mutate(gcda_list):
    pool = Pool(32)
    for gcda in gcda_list:
        pool.apply_async(mutate_single_gcda, (gcda,))
        # mutate_one_file(file_name)
    pool.close()
    pool.join()


def mutate_single_gcda(gcda):
    gcda.mutate()
    gcda.save()


def save_bug_report(file_name):
    # copy source code
    shutil.copyfile(file_name + "/" + file_name + ".c", "bug_report/" + file_name + "/" + file_name + ".c")
    # copy result
    shutil.copyfile(file_name + "/" + file_name + ".txt", "bug_report/" + file_name + "/" + file_name + ".txt")
    shutil.copyfile(file_name + "/" + file_name + "_mut.txt",
                    "bug_report/" + file_name + "/" + file_name + "_mut.txt")
    # copy gcda file
    shutil.copyfile(file_name + "/" + file_name + "_mut-" + file_name + ".gcda",
                    "bug_report/" + file_name + "/" + file_name + "_mut-" + file_name + ".gcda")
    # copy executable file
    shutil.copyfile(file_name + "/" + file_name + "_mut", "bug_report/" + file_name + "/" + file_name + "_mut")
    shutil.copyfile(file_name + "/" + file_name, "bug_report/" + file_name + "/" + file_name)

import os
import shutil
from multiprocessing import Pool

from gcda import GcdaInfo

TEST_NUMBER = 100


def init(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)
    os.chdir(dir_path)
    pool = Pool(32)
    for i in range(TEST_NUMBER):
        file_name = "test" + str(i)
        pool.apply_async(generate_compile, (file_name,))
    pool.close()
    pool.join()


def generate_compile(file_name):
    os.mkdir(file_name)
    generate_cmd = "csmith > " + file_name + "/" + file_name + ".c"
    compile_cmd = "gcc -fprofile-generate " + file_name + "/" + file_name + ".c -o " + file_name + "/" + file_name
    execute_cmd = "timeout 30s ./" + file_name + "/" + file_name
    result = 1
    while result != 0:
        os.system(generate_cmd)
        os.system(compile_cmd)
        result = os.system(execute_cmd)


def gcc_recompile():
    pool = Pool(32)
    for file_name in os.listdir('.'):
        cmd = "gcc -fprofile-use " + file_name + "/" + file_name + ".c -o " + file_name + "/" + file_name + "_mut"
        pool.apply_async(os.system, (cmd,))
    pool.close()
    pool.join()


def differential_test():
    os.makedirs("bug_report", exist_ok=True)
    pool = Pool(32)
    bug_report = open("bug_report.txt", "w")
    for file_name in os.listdir('.'):
        cmd = "./" + file_name + "/" + file_name + " > " + file_name + "/" + file_name + ".txt"
        cmd += "; ./" + file_name + "/" + file_name + "_mut > " + file_name + "/" + file_name + "_mut.txt"
        cmd += "; diff " + file_name + "/" + file_name + ".txt " + file_name + "/" + file_name + "_mut.txt"
        result = os.system(cmd)
        if result != 0:
            os.mkdir("bug_report/" + file_name)
            save_bug_report(file_name)
            # write to bug_report.txt
            bug_report.write(file_name + "\n")
            bug_report.flush()
        else:
            os.replace(file_name + "/" + file_name + "_mut-" + file_name + ".gcda",
                       file_name + "/" + file_name + ".gcda")
        os.remove(file_name + "/" + file_name + ".txt")
        os.remove(file_name + "/" + file_name + "_mut.txt")
        os.remove(file_name + "/" + file_name + "_mut")
        os.remove(file_name + "/" + file_name + "_mut-" + file_name + ".gcda")
    pool.close()
    pool.join()
    bug_report.close()


def mutate():
    pool = Pool(32)
    for file_name in os.listdir('.'):
        # pool.apply_async(mutate_one_file, (file_name,))
        mutate_one_file(file_name)
    pool.close()
    pool.join()


def mutate_one_file(file_name):
    gcda = GcdaInfo()
    print("load " + file_name + "/" + file_name + ".gcda")
    gcda.load(file_name + "/" + file_name + ".gcda")
    print(file_name + ".gcda pull records")
    gcda.pull_records()
    print(file_name + ".gcda mutate")
    gcda.mutate()
    gcda.save(file_name + "/" + file_name + "_mut-" + file_name + ".gcda")


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

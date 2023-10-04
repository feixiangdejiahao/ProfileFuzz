import os
import shutil
from multiprocessing import Pool

from gcda import GcdaInfo

TEST_NUMBER = 100


def generate(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)
    os.chdir(dir_path)
    pool = Pool(32)
    for i in range(TEST_NUMBER - 1):
        file_name = "test" + str(i)
        os.mkdir(file_name)
        cmd = "csmith > " + file_name + "/" + file_name + ".c"
        pool.apply_async(os.system, (cmd,))
    pool.close()
    pool.join()


def gcc_compile():
    pool = Pool(32)
    for file_name in os.listdir('.'):
        cmd = "gcc -fprofile-generate " + file_name + "/" + file_name + ".c -o " + file_name + "/" + file_name
        cmd += "; ./" + file_name + "/" + file_name
        print(cmd)
        pool.apply_async(os.system, (cmd,))
    pool.close()
    pool.join()


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
    pool.close()


def mutate():
    pool = Pool(32)
    for file_name in os.listdir('.'):
        pool.apply_async(mutate_one_file, (file_name,))
    pool.close()
    pool.join()


def mutate_one_file(file_name):
    gcda = GcdaInfo()
    gcda.load(file_name + "/" + file_name + ".gcda")
    gcda.pull_records()
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

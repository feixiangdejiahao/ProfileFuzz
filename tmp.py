from z3 import *

# 创建Z3求解器实例
solver = Solver()

# 定义变量
A = Int('A') # A的执行次数
B = Int('B') # B的执行次数
C = Int('C') # C的执行次数
D = Int('D') # D的执行次数

# 定义每个变量的范围
solver.add(And(A >= 13, A <= 100))  # 假设A的范围是3到10
solver.add(And(B >= 10, B <= 50))   # 假设B的范围是1到5
solver.add(And(C >= 21, C <= 70))   # 假设C的范围是2到7
solver.add(And(D >= 20, D <= 79))   # 假设D的范围是2到7

# 添加约束
solver.add(A == 2 * B + C) # A是B的两倍
solver.add(C == D)     # C和D的执行次数必须相等

# 找出所有可能的解
solutions = []
while solver.check() == sat:
    m = solver.model()
    solution = (m[A].as_long(), m[B].as_long(), m[C].as_long(), m[D].as_long())
    solutions.append(solution)

    # 防止重复解
    block = []
    for d in m:
        c = d()
        block.append(c != m[d])
    solver.add(Or(block))

# 打印所有解
for sol in solutions:
    print(f"A: {sol[0]}, B: {sol[1]}, C: {sol[2]}, D: {sol[3]}")

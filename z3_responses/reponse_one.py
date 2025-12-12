from z3 import *

x, y, z, w, v, u, a, b = Bools('x y z w v u a b')

hypothesis = And(x, Or(y, z), Not(w), Xor(v, u), a, b)
conclusion = Or(Not(x), And(Not(y), Not(z)), w, Not(Xor(v, u)), Not(a), Not(b))

solver = Solver()
solver.add(Not(Implies(hypothesis, conclusion)))
result = solver.check()

if result == unsat:
    print("The conclusion is a logical consequence of the hypotheses.")
else:
    print("The conclusion is NOT a logical consequence of the hypotheses.")
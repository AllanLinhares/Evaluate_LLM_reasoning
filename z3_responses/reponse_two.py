from z3 import *
x, y, z, w, v, u, a, b = Bools('x y z w v u a b')
hypothesis = And(x, y, Not(z), w, v)
conclusion = Or(z, Xor(x, u), Xor(y, a), Not(b))
solver = Solver()
solver.add(Not(Implies(hypothesis, conclusion)))
result = solver.check()
if result == unsat:
    print("The conclusion is a logical consequence of the hypotheses.")
else:
    print("The conclusion is NOT a logical consequence of the hypotheses.")
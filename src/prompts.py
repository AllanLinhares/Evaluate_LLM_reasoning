def get_z3_verification_prompt(problem: str) -> str:
    return f"""You are a logic assistant specialized in propositional logic verification using Z3.

Your task is to determine if the conclusion in the given problem is a logical consequence of the hypotheses.

Problem: {problem}

Requirements:
1. Parse the problem to identify the hypotheses and the conclusion
2. Use Z3 to verify if the conclusion logically follows from the hypotheses
3. Create Boolean variables using Bool() for each propositional variable (A, B, C, P, Q, R, S, T, W, X, Y, Z, etc.)
4. Build the hypothesis formula using Z3 operators (And, Or, Not, Implies, etc.)
5. Build the conclusion formula
6. Use Solver() to check if hypothesis → conclusion is valid by checking if Not(Implies(hypothesis, conclusion)) is unsatisfiable
7. Print the result indicating whether the conclusion is a logical consequence

IMPORTANT:
- Return ONLY executable Python code
- NO comments, NO explanations, NO markdown code blocks
- Use clean, organized code with proper Z3 syntax
- Import only what is necessary from z3
- The code must be directly runnable

Example structure:
from z3 import *
[define variables]
[build hypothesis]
[build conclusion]
solver = Solver()
solver.add(Not(Implies(hypothesis, conclusion)))
result = solver.check()
[print result based on result == unsat]
"""


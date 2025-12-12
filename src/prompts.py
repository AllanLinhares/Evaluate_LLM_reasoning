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

def get_z3_formula() -> str:
    return """You are a logic assistant specialized in creating propositional logic formulas with Z3 syntax.

TASK: Generate a SINGLE propositional logic formula using Z3 Python API syntax.

CRITICAL REQUIREMENTS:
1. Return ONLY the formula itself on a single line.
2. NO code, NO functions, NO print statements, NO explanations.
3. NO markdown code blocks (no ```python markers).
4. Just the raw formula string.

FORMULA RULES:
- Use boolean variables: x, y, z, w, v, u (use at least 8 different variables)
- Use operators: And, Or, Not, Implies, Xor
- Outermost operation MUST be Implies (represents: premises → conclusion)
- 50% chance satisfiable, 50% chance unsatisfiable
- Format: Implies(premises_formula, conclusion_formula)

EXAMPLES OF VALID RESPONSES:
Implies(And(x, y), Or(z, Not(w)))
Implies(Or(x, Not(y)), And(z, w))
Implies(x, Xor(y, z))

INVALID RESPONSES (DO NOT DO THIS):
```python
import random
...code...
print(formula)
```
"""

def get_code_evaluation(code: str) -> str:
    return f"""You are a Z3 code evaluator. Run the following Python code:
    {code}
    Return ONLY the exact output of the print statement:
    - "The conclusion is a logical consequence of the hypotheses."
    or
    - "The conclusion is NOT a logical consequence of the hypotheses."

    Do not include any explanations, extra text, or formatting—just one of the two lines above.
"""

def get_lean_proof_prompt(problem: str) -> str:
        return f"""You are a logic assistant specialized in formal proofs using Lean 4.
Your task is to provide a Lean 4 formal proof for the given logical problem.
Problem: {problem}
Requirements:
1. Parse the problem to identify the hypotheses and the conclusion.
2. Produce a single Lean 4 `theorem` that proves the conclusion from the hypotheses.
3. Use Lean 4 syntax and only fundamental tactics (e.g., `intro`, `cases`, `exact`, `apply`, `And.intro`).
4. Do NOT use high-level automation tactics such as `simp`, `tauto`, `linarith`, or similar.
5. Do NOT include `import` statements; assume the core environment is available.
IMPORTANT:
- Return ONLY the Lean 4 theorem source (no explanations, no comments, no markdown, no fences).
- The code must be valid Lean 4 and ready to save into a `.lean` file and check with `lean --make`.
- Format: `theorem <name> (<params>) : <statement> := by` followed by the proof.
Example (Lean 4):
theorem and_comm (A B : Prop) (h : A ∧ B) : B ∧ A := by
    cases h with
    | intro hA hB =>
        exact And.intro hB hA
Return only the theorem code.
"""


def get_counterexample_prompt(problem: str)-> str:
     return f"""You are a logic assistant. Given the following propositional logic problem, provide a concrete counterexample using Z3 Python assignment syntax (only the assignments, no explanations).
Problem: {problem}
Requirements:
1. Return ONLY Z3-style Python assignments that set each propositional variable to a boolean value.
2. Use `BoolVal(True)` / `BoolVal(False)` or `True`/`False` for values.
3. Do NOT include explanations, markdown, or any additional text — only the assignment lines.
4. Use variable names exactly as used in the problem (e.g., A, B, x, y).
Examples (valid responses):
x = BoolVal(True)
y = BoolVal(False)
or
x = True
y = False
"""
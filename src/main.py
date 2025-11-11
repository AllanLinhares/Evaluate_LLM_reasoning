import json
import os
from dotenv import load_dotenv
import google.genai as genai
from z3 import *

def z3_solver():
    A = Bool('A')
    B = Bool('B')
    hypothesis = And(B, A)
    goal = And(A, B)

    solver = Solver()
    solver.add(Not(Implies(hypothesis, goal)))
    result = solver.check()

    if result == unsat:
        print("✅ Proven: From (B ∧ A), we can derive (A ∧ B).")
    else:
        print("❌ Not valid. Counterexample:", solver.model())

def connect_gemini(prompt: str):
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: API key not found!!!")
        return None
    
    client = genai.Client(api_key=api_key)
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=(
            "You are a helpful assistant that can help with natural deduction proofs. "
            "You must respond ONLY with Z3 code. "
            "DO NOT return anything but the Z3 code. "
            "No comments, no imports, no explanations, no greetings, no text before or after. "
            "The Z3 code must check if the conclusion is a logical consequence of the premises. "
            "Use a Solver, add the premises, add the negation of the conclusion, and check satisfiability. "
            "ONLY the pure Z3 code to solve the following propositional logic problem: " + prompt
        ),
    )
    
    z3_code = response.text.strip()
    
    if z3_code.startswith("```"):
        lines = z3_code.split('\n')
        z3_code = '\n'.join(lines[1:-1]) if lines[-1].strip() == "```" else '\n'.join(lines[1:])
    
    print(prompt)
    print("--------------------------------")
    print("Z3 Code received:")
    print(z3_code)
    print("--------------------------------")

    z3_solver()

def retrieve_premisses():
    if os.path.exists('utils/premises.json'):
        with open('utils/premises.json', 'r') as file:
            return json.load(file)
    else:
        return None

def main():
    premisse = retrieve_premisses()["1"]
    connect_gemini(premisse)


if __name__ == "__main__":
    main()

import json
import os
import io
import contextlib
from dotenv import load_dotenv
from google import genai
from z3 import *
from prompts import get_z3_verification_prompt

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

def remove_code_block_markers(code: str) -> str:
    code = code.strip()

    if code.startswith('```'):
        lines = code.split('\n')
        if lines[0].startswith('```'):
            lines = lines[1:]
        code = '\n'.join(lines)

    if code.endswith('```'):
        code = code[:-3].rstrip()
    
    return code.strip()

def agent_to_code_parser(code: str) -> str:
    namespace = {}
    with io.StringIO() as buf, contextlib.redirect_stdout(buf):
        try:
            exec(code, namespace)
            return buf.getvalue()
        except Exception as e:
            return f"Error: {e}"

def connect_gemini(problem: str):
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: API key not found!!!")
        return None

    client = genai.Client(api_key=api_key)

    prompt = get_z3_verification_prompt(problem)

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt
    )

    print("Gemini response START ########################################:\n")
    print(response.text.strip())
    print("Gemini response END ########################################:\n")

    code = remove_code_block_markers(response.text)
    print("RUNNING LLM CODE START ########################################:\n")
    output = agent_to_code_parser(code)
    print(output)
    print("RUNNING LLM CODE START ########################################:\n")

def retrieve_premisses():
    if os.path.exists('utils/premises.json'):
        with open('utils/premises.json', 'r') as file:
            return json.load(file)
    else:
        return None

def main():
    premisse = retrieve_premisses()["7"]
    connect_gemini(premisse)
    

if __name__ == "__main__":
    main()
import json
import os
import io
import contextlib
from dotenv import load_dotenv
from google import genai
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type, RetryError
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

def is_valid_formula(formula: str) -> bool:

    if not formula or not isinstance(formula, str):
        return False
    
    formula = formula.strip()
    
    #se está vazio
    if not formula:
        return False
    
    if formula.startswith('//') or formula == "//":
        return False
    
    #fórmulas válidas
    valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz∧∨→¬↔&|()[]{} ,→¬')
    if not any(c in formula for c in valid_chars):
        return False
    
    return True

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
    
    @retry(
        wait=wait_exponential_jitter(),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(genai.errors.ServerError),
    )
    def _generate_with_retry(client, prompt):
        return client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

    try:
        response = _generate_with_retry(client, prompt)
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        print(f"Error: exhausted retries when calling Gemini: {last}")
        return None
    
    except genai.errors.ServerError as e:
        print(f"ServerError from Gemini: {e}")
        return None

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
    premisses = retrieve_premisses()
    if not premisses:
        print("Error: Could not load premises from utils/premises.json")
        return
    
    premisse = premisses.get("7")
    
    if not premisse:
        print("Error: Premise not found in premises.json")
        return
    
    if not is_valid_formula(premisse):
        print(f"Error: Premise '{premisse}' is not a valid logical formula.")
        print("Please provide a valid logical formula (e.g., 'A ∧ B → C').")
        return
    
    connect_gemini(premisse)

if __name__ == "__main__":
    main()
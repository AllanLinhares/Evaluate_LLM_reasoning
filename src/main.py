import json
import os
import io
import contextlib
import argparse
from dotenv import load_dotenv
from google import genai
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type, RetryError
from z3 import *
from prompts import get_z3_verification_prompt, get_z3_formula

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


def save_generated_formula(formula: str, filepath: str = 'results/generated_formulas.json'):

    entries = []
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                entries = json.load(f) or []
        except Exception:
            try:
                backup = f"{filepath}.bak"
                os.replace(filepath, backup)
                print(f"Warning: corrupted results file moved to {backup}")
            except Exception:
                print("Warning: failed to back up corrupted results file; overwriting.")
            entries = []

    entry_id = len(entries) + 1
    entry = {"id": entry_id, 
             "formula": formula
             }
    entries.append(entry)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    return entry


def generate_formula_via_llm() -> str:

    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        raise ValueError("Error: API key not found!!!")

    client = genai.Client(api_key=api_key)
    prompt = get_z3_formula()

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
        raise RuntimeError(f"Error: exhausted retries when calling Gemini: {last}")
    except genai.errors.ServerError as e:
        raise RuntimeError(f"ServerError from Gemini: {e}")

    formula = response.text.strip()
    
    formula = remove_code_block_markers(formula)
    
    #extrai ultima linha se resposta tiver várias
    if '\n' in formula:
        lines = [line.strip() for line in formula.split('\n') if line.strip()]
        if lines:
            formula = lines[-1]
    
    return formula


def generate_and_save_formula(filepath: str = 'results/generated_formulas.json') -> dict:

    formula = generate_formula_via_llm()
    if not formula or not isinstance(formula, str) or not formula.strip():
        raise ValueError('LLM did not return a valid formula string')

    return save_generated_formula(formula.strip(), filepath)


def load_generated_formulas(filepath: str = 'results/generated_formulas.json') -> list:

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Generated formulas file not found: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        entries = json.load(f) or []

    return entries


def get_formula_by_id(formula_id: int, filepath: str = 'results/generated_formulas.json') -> str:

    entries = load_generated_formulas(filepath)
    for entry in entries:
        if entry.get('id') == formula_id:
            return entry.get('formula', '')
    
    raise KeyError(f"Formula with id={formula_id} not found in {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM reasoning with Z3")
    parser.add_argument('--generate', action='store_true', help='Generate a formula and save it to results/generated_formulas.json')
    parser.add_argument('--formula-id', type=int, help='Formula id to load from results/generated_formulas.json')
    parser.add_argument('--premise-id', default='1', help='Premise id to load from utils/premises.json (used if --formula-id not provided)')
    args = parser.parse_args()

    if args.generate:
        try:
            saved = generate_and_save_formula()
            print(f"Saved generated formula id={saved['id']} to results/generated_formulas.json")
        except Exception as e:
            print(f"Error generating/saving formula: {e}")
        return

    #Usa formulas geradas
    if args.formula_id is not None:
        try:
            formula = get_formula_by_id(args.formula_id)
            print(f"Using generated formula id={args.formula_id}: {formula}")
            connect_gemini(formula)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return
        except KeyError as e:
            print(f"Error: {e}")
            return
        return

    #Usa premissas, comportamento padrão
    premisses = retrieve_premisses()
    if not premisses:
        print("Error: Could not load premises from utils/premises.json")
        return

    premisse = premisses.get(args.premise_id)

    if not premisse:
        print(f"Error: Premise '{args.premise_id}' not found in premises.json")
        return

    if not is_valid_formula(premisse):
        print(f"Error: Premise '{premisse}' is not a valid logical formula.")
        print("Please provide a valid logical formula (e.g., 'A ∧ B → C').")
        return

    connect_gemini(premisse)

if __name__ == "__main__":
    main()
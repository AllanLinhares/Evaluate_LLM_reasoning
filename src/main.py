import json
import os
import io
import contextlib
import argparse
import subprocess
from dotenv import load_dotenv
from google import genai
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type, RetryError
from z3 import *
from prompts import get_z3_verification_prompt, get_z3_formula, get_lean_proof_prompt, get_counterexample_prompt

# Load environment variables once at module import time to avoid repeated calls
load_dotenv()


def remove_code_block_markers(code: str) -> str:
    if code is None:
        return ''
    code = code.strip()
    if code.startswith('```'):
        parts = code.split('\n')
        if parts and parts[0].startswith('```'):
            parts = parts[1:]
        code = '\n'.join(parts)
    if code.endswith('```'):
        code = code[:-3].rstrip()
    return code.strip()


def is_valid_formula(formula: str) -> bool:
    if not formula or not isinstance(formula, str):
        return False
    f = formula.strip()
    if not f:
        return False
    if f.startswith('//'):
        return False
    return True


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
    entry = {"id": entry_id, "formula": formula, "status": "new", "proof_path": None, "verification": None}
    entries.append(entry)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    return entry


def load_generated_formulas(filepath: str = 'results/generated_formulas.json') -> list:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f) or []


def get_formula_by_id(formula_id: int, filepath: str = 'results/generated_formulas.json') -> str:
    entries = load_generated_formulas(filepath)
    for entry in entries:
        if entry.get('id') == formula_id:
            return entry
    raise KeyError(f"Formula with id={formula_id} not found in {filepath}")


def update_generated_formula(entry_id: int, updates: dict, filepath: str = 'results/generated_formulas.json'):
    entries = load_generated_formulas(filepath)
    found = False
    for i, entry in enumerate(entries):
        if entry.get('id') == entry_id:
            entries[i] = {**entry, **updates}
            found = True
            break
    if not found:
        raise KeyError(f"Formula with id={entry_id} not found in {filepath}")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    return entries[i]


def generate_formula_via_llm() -> str:
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
        return client.models.generate_content(model='gemini-2.5-flash', contents=prompt)

    try:
        response = _generate_with_retry(client, prompt)
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        raise RuntimeError(f"Error: exhausted retries when calling Gemini: {last}")
    except genai.errors.ServerError as e:
        raise RuntimeError(f"ServerError from Gemini: {e}")

    formula = remove_code_block_markers(response.text.strip())
    lines = [ln.strip() for ln in formula.splitlines() if ln.strip()]
    if lines:
        return lines[-1]
    return formula


def request_lean_proof(problem: str) -> str:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("Error: API key not found!!!")

    client = genai.Client(api_key=api_key)
    prompt = get_lean_proof_prompt(problem)

    @retry(
        wait=wait_exponential_jitter(),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(genai.errors.ServerError),
    )
    def _generate_with_retry(client, prompt):
        return client.models.generate_content(model='gemini-2.5-flash', contents=prompt)

    try:
        response = _generate_with_retry(client, prompt)
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        raise RuntimeError(f"Error: exhausted retries when calling Gemini: {last}")
    except genai.errors.ServerError as e:
        raise RuntimeError(f"ServerError from Gemini: {e}")

    return remove_code_block_markers(response.text.strip())


def check_lean_proof(filepath: str = 'src/lean/proof_temp.lean') -> dict:
    """Run `lean --make <filepath>` if available and return a dict with returncode, stdout, stderr."""
    try:
        proc = subprocess.run(['lean', '--make', filepath], capture_output=True, text=True)
        return {
            'returncode': proc.returncode,
            'stdout': proc.stdout,
            'stderr': proc.stderr,
        }
    except FileNotFoundError:
        return {'error': 'lean not found on PATH'}
    except Exception as e:
        return {'error': str(e)}


def execute_lean_proof(lean_code: str, filepath: str = 'src/lean/proof_temp.lean', entry_id: int = None) -> bool:
    dirpath = os.path.dirname(filepath) or 'src/lean'
    if dirpath and not os.path.exists(dirpath):
        os.makedirs(dirpath, exist_ok=True)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(lean_code)
        print(f"LEAN proof saved to {filepath}")
    except Exception as e:
        print(f"Error writing LEAN proof: {e}")
        return False

    print(f"LEAN proof code:\n{lean_code}")

    # If an entry id was provided, persist the proof text/path into results JSON
    if entry_id is not None:
        try:
            update_generated_formula(entry_id, {'proof_path': filepath, 'proof_text': lean_code})
        except Exception as e:
            print(f"Warning: failed to update generated formula with proof: {e}")

    return True


def request_counterexample_z3(problem: str) -> str:
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("Error: API key not found!!!")

    client = genai.Client(api_key=api_key)
    prompt = get_counterexample_prompt(problem)

    @retry(
        wait=wait_exponential_jitter(),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(genai.errors.ServerError),
    )
    def _generate_with_retry(client, prompt):
        return client.models.generate_content(model='gemini-2.5-flash', contents=prompt)

    try:
        response = _generate_with_retry(client, prompt)
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        raise RuntimeError(f"Error: exhausted retries when calling Gemini: {last}")
    except genai.errors.ServerError as e:
        raise RuntimeError(f"ServerError from Gemini: {e}")

    return remove_code_block_markers(response.text.strip())



 

def run_z3_verifier(code_str: str, timeout_seconds: int = 10) -> dict:
    """Execute Z3 verifier code returned by LLM by running it in-process and capture its stdout.

    This follows the `agent_to_code_parser` pattern: execute the code in a fresh namespace
    (with default builtins) and capture printed output. Returns dict with keys:
    'stdout', 'token' ('unsat'|'sat'|'unknown'|None), and 'error' (if execution failed).
    """
    if not isinstance(code_str, str):
        return {'stdout': '', 'token': None, 'error': 'code_str must be a string'}

    def agent_to_code_parser(code: str) -> str:
        namespace = {}
        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            try:
                exec(code, namespace)
                return buf.getvalue()
            except Exception as e:
                return f"Error: {e}"

    out = agent_to_code_parser(code_str)
    if out.startswith('Error:'):
        return {'stdout': out, 'token': None, 'error': out}

    token = None
    lines = [ln.strip().lower() for ln in out.splitlines() if ln.strip()]
    if lines:
        last = lines[-1]
        if last in ('unsat', 'sat', 'unknown'):
            token = last
    if token is None:
        low = out.lower() if out else ''
        if 'unsat' in low or 'unsatisfiable' in low:
            token = 'unsat'
        elif 'sat' in low:
            token = 'sat'
        elif 'unknown' in low:
            token = 'unknown'

    return {'stdout': out, 'token': token, 'error': None}


def connect_gemini(problem: str, entry_id: int = None):
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

    z3_response = response.text.strip()
    print("Gemini (Z3) response START ########################################:\n")
    print(z3_response)
    print("Gemini (Z3) response END ########################################:\n")

    # Normalize response (remove fences)
    z3_response_clean = remove_code_block_markers(z3_response)

    # Prepare result container and prefer executing the returned verifier code in a restricted namespace
    result = {'z3_response': None, 'z3_exec': None}
    exec_result = run_z3_verifier(z3_response_clean)
    # attach raw LLM response and execution result to result for debugging
    result['z3_response'] = z3_response_clean
    result['z3_exec'] = exec_result

    if exec_result.get('error') is None and exec_result.get('token') is not None:
        result_token = exec_result.get('token')
        print(f"Executed verifier stdout:\n{exec_result.get('stdout')}")
        print(f"Parsed Z3 verifier token (from execution): '{result_token}'")
    else:
        # Fallback: try to parse the LLM text directly
        if exec_result.get('error'):
            print(f"Verifier execution error: {exec_result.get('error')}")
        lines = [ln.strip() for ln in z3_response_clean.splitlines() if ln.strip()]
        final_token = lines[-1].lower() if lines else z3_response_clean.lower()
        if final_token in ('unsat', 'sat', 'unknown'):
            result_token = final_token
        else:
            if 'unsat' in z3_response_clean.lower() or 'unsatisfiable' in z3_response_clean.lower():
                result_token = 'unsat'
            elif 'sat' in z3_response_clean.lower():
                result_token = 'sat'
            else:
                result_token = 'unknown'
        print(f"Parsed Z3 verifier token (from text): '{result_token}'")

    is_consequence = (result_token == 'unsat')

    # Persist z3 execution/debug info into JSON metadata when entry_id provided
    if entry_id is not None:
        try:
            update_generated_formula(entry_id, {'verification': {'result_token': result_token, 'z3_response': z3_response_clean, 'z3_exec': exec_result}})
        except Exception as e:
            print(f"Warning: failed to persist z3 execution info: {e}")

    result.update({
        'result_token': result_token,
        'is_consequence': is_consequence,
        'lean_code': None,
        'counterexample_code': None,
        'counterexample_verification': None,
    })

    if is_consequence:
        print("\n✅ Conclusion is a logical consequence according to Z3. Requesting LEAN proof from LLM...")
        try:
            lean_code = request_lean_proof(problem)
            target_path = f'src/lean/proof_{entry_id}.lean' if entry_id is not None else 'src/lean/proof_temp.lean'
            ok = execute_lean_proof(lean_code, filepath=target_path, entry_id=entry_id)
            result['lean_code'] = lean_code
            result['lean_saved'] = ok

            # Try to run lean --make to validate the proof (if lean is installed)
            lean_check = check_lean_proof(filepath=target_path)
            result['lean_check'] = lean_check
            if entry_id is not None and isinstance(lean_check, dict):
                try:
                    update_generated_formula(entry_id, {'lean_check': lean_check, 'proof_path': target_path})
                except Exception as e:
                    print(f"Warning: failed to update generated formula with lean_check: {e}")
        except Exception as e:
            print(f"Error generating or saving LEAN proof: {e}")
            result['lean_error'] = str(e)
    else:
        print("\n❌ Conclusion is NOT a logical consequence (or Z3 returned a model). Requesting counterexample from LLM in Z3 assignment syntax...")
        try:
            code = request_counterexample_z3(problem)
            result['counterexample_code'] = code
            print("Counterexample (Z3 assignment code):\n")
            print(code)
            # Verify the counterexample code by executing the assignments and
            # evaluating the hypothesis and conclusion in-process (inline logic).
            try:
                s = problem.strip()
                hyp_str = None
                concl_str = None

                # Try to parse Implies(...)
                if 'Implies(' in s:
                    inside = s[s.find('Implies(') + len('Implies('):]
                    if inside.endswith(')'):
                        inside = inside[:-1]
                    depth = 0
                    split_index = None
                    for i, ch in enumerate(inside):
                        if ch == '(':
                            depth += 1
                        elif ch == ')':
                            depth -= 1
                        elif ch == ',' and depth == 0:
                            split_index = i
                            break
                    if split_index is not None:
                        hyp_str = inside[:split_index].strip()
                        concl_str = inside[split_index + 1 :].strip()

                # Fallback: split on arrows
                if hyp_str is None or concl_str is None:
                    for sep in ['->', '→', '=>']:
                        if sep in s:
                            parts = s.split(sep)
                            if len(parts) >= 2:
                                hyp_str = parts[0].strip()
                                concl_str = sep.join(parts[1:]).strip()
                                break

                if hyp_str is None or concl_str is None:
                    raise RuntimeError('Could not parse hypothesis and conclusion from problem string')

                allowed = {
                    'And': And,
                    'Or': Or,
                    'Not': Not,
                    'Implies': Implies,
                    'Xor': Xor,
                    'BoolVal': BoolVal,
                    'Bool': Bool,
                    'True': True,
                    'False': False,
                    'simplify': simplify,
                }

                ns = dict(allowed)

                with io.StringIO() as buf, contextlib.redirect_stdout(buf):
                    try:
                        exec(code, ns)
                        exec_out = buf.getvalue()
                        exec_err = None
                    except Exception as e:
                        exec_out = None
                        exec_err = f"Failed executing counterexample code: {e}\nCode:\n{code}"

                if exec_err is not None:
                    raise RuntimeError(exec_err)

                try:
                    hyp_eval = eval(hyp_str, {}, ns)
                    concl_eval = eval(concl_str, {}, ns)
                except Exception as e:
                    raise RuntimeError(f"Failed to evaluate hypothesis/conclusion: {e}")

                def _to_bool(v):
                    try:
                        return is_true(v)
                    except Exception:
                        try:
                            return bool(v)
                        except Exception:
                            return str(simplify(v)) == 'True'

                hyp_val = _to_bool(hyp_eval)
                concl_val = _to_bool(concl_eval)

                verified = bool(hyp_val) and (not bool(concl_val))

                assignments = {}
                for k, v in ns.items():
                    if k in allowed:
                        continue
                    try:
                        assignments[k] = bool(v) if not hasattr(v, 'eq') else _to_bool(v)
                    except Exception:
                        try:
                            assignments[k] = _to_bool(v)
                        except Exception:
                            assignments[k] = str(v)

                verification = {
                    'verified': verified,
                    'hypothesis_value': bool(hyp_val),
                    'conclusion_value': bool(concl_val),
                    'hypothesis_expr': hyp_str,
                    'conclusion_expr': concl_str,
                    'assignments': assignments,
                    'exec_stdout': exec_out,
                }

                result['counterexample_verification'] = verification
                print("Counterexample verification result:", verification.get('verified'))
                print("Verification details:")
                print(json.dumps(verification, indent=2, ensure_ascii=False))
            except Exception as e:
                print(f"Error verifying counterexample with Z3: {e}")
                result['counterexample_error'] = str(e)
        except Exception as e:
            print(f"Error requesting/parsing counterexample: {e}")
            result['counterexample_error'] = str(e)

    return result


def retrieve_premisses():
    if os.path.exists('utils/premises.json'):
        with open('utils/premises.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        return None


def generate_and_save_formula(filepath: str = 'results/generated_formulas.json') -> dict:
    formula = generate_formula_via_llm()
    if not formula or not isinstance(formula, str) or not formula.strip():
        raise ValueError('LLM did not return a valid formula string')

    return save_generated_formula(formula.strip(), filepath)


def main():
    parser = argparse.ArgumentParser(description="Evaluate LLM reasoning with Z3")
    parser.add_argument('--generate', action='store_true', help='Generate a formula and save it to results/generated_formulas.json')
    parser.add_argument('--formula-id', type=int, help='Formula id to load from results/generated_formulas.json')
    parser.add_argument('--force', action='store_true', help='Force re-run verification even if formula was already processed')
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
            entry = get_formula_by_id(args.formula_id)
            formula = entry.get('formula')
            print(f"Using generated formula id={args.formula_id}: {formula}")

            # If already processed and not forced, show saved status and skip re-run
            if entry.get('status') and entry.get('status') != 'new' and not args.force:
                print(f"Formula id={args.formula_id} has status='{entry.get('status')}'. Use --force to re-run verification.")
                if entry.get('verification'):
                    print("Saved verification:")
                    print(json.dumps(entry.get('verification'), indent=2, ensure_ascii=False))
                if entry.get('proof_path'):
                    print(f"Proof path: {entry.get('proof_path')}")
                return

            result = connect_gemini(formula, entry_id=args.formula_id)

            updates = {}
            if result is None:
                updates['status'] = 'error'
                updates['verification'] = {'error': 'No result from connect_gemini'}
            else:
                if result.get('is_consequence'):
                    updates['status'] = 'proved'
                    updates['proof_path'] = 'src/lean/proof_temp.lean' if result.get('lean_saved') else None
                    updates['verification'] = {'result_token': result.get('result_token'), 'lean_saved': result.get('lean_saved', False)}
                else:
                    verified = None
                    if result.get('counterexample_verification'):
                        verified = result['counterexample_verification'].get('verified')
                    updates['status'] = 'counterexample_verified' if verified else 'counterexample_unverified'
                    updates['verification'] = result.get('counterexample_verification') or {'result_token': result.get('result_token')}

            try:
                update_generated_formula(args.formula_id, updates)
            except Exception as e:
                print(f"Warning: failed to update generated formula metadata: {e}")

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
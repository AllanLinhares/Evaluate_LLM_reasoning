import json
import os
import io
import contextlib
from dotenv import load_dotenv
from google import genai
from tenacity import retry, wait_exponential_jitter, stop_after_attempt, retry_if_exception_type, RetryError
from z3 import *
from prompts import get_z3_formula, get_z3_verification_prompt, get_code_evaluation, get_lean_proof_prompt

def askGeminiLogicProblem() -> str:
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: API key not found!!!")
        return None

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
        return response.text.strip()
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        print(f"Error: exhausted retries when calling Gemini: {last}")
        return None
    
    except genai.errors.ServerError as e:
        print(f"ServerError from Gemini: {e}")
        return None

def solveProblemWithZ3(formula: str) -> str:
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: API key not found!!!")
        return None

    client = genai.Client(api_key=api_key)

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
    
    prompt = get_z3_verification_prompt(formula)

    try:
        response = _generate_with_retry(client, prompt)
        return response.text.strip()
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        print(f"Error: exhausted retries when calling Gemini: {last}")
        return None
    
    except genai.errors.ServerError as e:
        print(f"ServerError from Gemini: {e}")
        return None

def ask_gemini_to_solve_z3_code(z3_code: str) -> str:
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: API key not found!!!")
        return None

    client = genai.Client(api_key=api_key)

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
    
    prompt = get_code_evaluation(z3_code)

    try:
        response = _generate_with_retry(client, prompt)
        return response.text.strip()
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        print(f"Error: exhausted retries when calling Gemini: {last}")
        return None
    
    except genai.errors.ServerError as e:
        print(f"ServerError from Gemini: {e}")
        return None
    
def request_lean_proof(problem: str) -> str:
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("Error: API key not found!!!")
        return None

    client = genai.Client(api_key=api_key)

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
    
    prompt = get_lean_proof_prompt(problem)

    try:
        response = _generate_with_retry(client, prompt)
        return response.text.strip()
    except RetryError as e:
        last = e.last_attempt.exception() if hasattr(e, 'last_attempt') else e
        print(f"Error: exhausted retries when calling Gemini: {last}")
        return None
    
    except genai.errors.ServerError as e:
        print(f"ServerError from Gemini: {e}")
        return None

def execute_generated_code(code: str) -> str:
    # Remove formatação markdown se presente
    clean_code = code.strip()
    if clean_code.startswith("```python"):
        clean_code = clean_code.replace("```python", "", 1)
    elif clean_code.startswith("```"):
        clean_code = clean_code.replace("```", "", 1)
    
    if clean_code.endswith("```"):
        clean_code = clean_code[:-3]
    
    clean_code = clean_code.strip()
    f = io.StringIO()
    try:
        with contextlib.redirect_stdout(f):
            exec(clean_code, globals())
        return f.getvalue()
    except Exception as e:
        return f"Erro ao executar o código gerado: {e}"

def main():
    logicProblem = askGeminiLogicProblem()
    z3LLMCode = solveProblemWithZ3(logicProblem)
    execution_result = execute_generated_code(z3LLMCode)
    evaluation = ask_gemini_to_solve_z3_code(z3LLMCode)
    lean_prompt = request_lean_proof(logicProblem)

    print(f"▶️ Problema gerado: {logicProblem}")
    print("-----")
    print(f"▶️ Código Z3 gerado:\n{z3LLMCode}")
    print("-----")
    print("▶️ Resultado da execução local:")
    print(execution_result)
    print("-----")
    print(f"▶️ Resultado da execução da LLM:\n{evaluation}")
    print("-----")
    print(f"▶️ Prova formal em Lean 4:\n{lean_prompt}")

if __name__ == "__main__":
    main()
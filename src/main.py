import os
import json
from dotenv import load_dotenv
from google import genai

def get_premises():
    with open('utils/premises.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def main():
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("Error: GOOGLE_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key.")
        return

    client = genai.Client(api_key=api_key)

    premises = get_premises()
    problem = premises["1"]
    print(problem)
    prompt = (f"## Zero-Shot Natural Deduction Task"
              f"**Role:** You are an expert formal logician and a Lean Theorem Prover assistant. Your task is to provide two solutions for the given logical problem."
              f"**Goal:** For the given theorem, provide a natural deduction proof AND the corresponding formal proof in Lean 4 syntax."
              f"**Constraints:**"
              f"1.  **Do not** use any theorem-proving tactics (`by simp`, `by linarith`, `by tauto`, etc.) in the Lean proof. Only use fundamental tactics like `intro`, `exact`, `apply`, `split`, `cases`, `refine`, etc., to demonstrate explicit, step-by-step logic."
              f"2.  Provide the output in the exact JSON format specified below."
              f"3.  Do not include any Lean imports (e.g., `import Mathlib.Tactic.Basic`). Assume the necessary core logic environment is set up."
              f"---"
              f"**Problem:**"
              f"**Theorem:** {problem}"
              f"---")

    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=prompt
    )

    print("Gemini response:")
    print(response.text)

if __name__ == "__main__":
    main()

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

    response = client.models.generate_content(
        model='gemini-2.0-flash-exp',
        contents=problem
    )

    print("Gemini response:")
    print(response.text)

if __name__ == "__main__":
    main()

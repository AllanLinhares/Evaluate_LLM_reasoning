# LLM Logical Reasoning Evaluator

## Implementation Steps

### 1. Create Core Script Structure (`src/main.py`)
- Load premises from `utils/premises.json`
- Accept command-line argument to select which problem to evaluate (default: problem 1)
- Load Google Gemini API key from environment variable (GOOGLE_API_KEY)
- Initialize Google Gemini Flash 2.5 client using the `google-genai` library

### 2. Implement LLM Query Logic
- Create function to query Gemini with two-stage approach:
  - **Stage 1**: Send the natural deduction problem and ask for a detailed natural deduction proof
  - **Stage 2**: Ask the LLM to translate the same problem into a LEAN 3 proof
- Use appropriate prompts that reference the LEAN documentation link from README
- Handle API errors gracefully

### 3. Results Display and Storage
- Display results to console:
  - Problem statement
  - Natural deduction proof response
  - LEAN proof response
- Save complete results to `results/` directory as JSON files with timestamp
- Each result file should include:
  - Problem ID and statement
  - Natural deduction proof
  - LEAN proof
  - Timestamp
  - Model used

### 4. Configuration
- Create `.env.example` file showing required environment variables
- Update `.gitignore` to include `results/` directory
- Add brief usage instructions to README

## Key Files to Modify
- `src/main.py` - Main script implementation
- Create `results/` directory for output storage
- Create `.env.example` for API key template

## Technical Details
- Use `google.genai` library (already in requirements.txt)
- Use `python-dotenv` for environment variables (already in requirements.txt)
- JSON for structured data handling
- Command-line interface: `python src/main.py [problem_number]`

## Todos
1. Load premises from utils/premises.json and implement problem selection
2. Initialize Google Gemini Flash 2.5 client with API key from environment
3. Implement functions to query LLM for natural deduction and LEAN proofs
4. Create results directory structure and implement JSON output saving
5. Add command-line argument parsing for problem selection
6. Create .env.example and update README with usage instructions


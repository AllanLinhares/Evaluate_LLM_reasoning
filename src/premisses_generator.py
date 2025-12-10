import random
import json
import sys

VARS = ["p", "q", "r"]


def rand_var():
    return random.choice(VARS)


def rand_formula(depth=2):
    if depth == 0:
        v = rand_var()
        return v if random.random() < 0.7 else f"¬{v}"
    op = random.choice(["¬", "∧", "∨", "→", "↔"])
    if op == "¬":
        return f"¬({rand_formula(depth-1)})"
    left = rand_formula(depth-1)
    right = rand_formula(depth-1)
    return f"({left} {op} {right})"


def premises_generator(n=3, depth=2):
    return [rand_formula(depth) for _ in range(n)]
    

def save_premises_to_json(premises):
    # monta o dicionário numerado
    data = {str(i+1): prem for i, prem in enumerate(premises)}
    with open('utils/auto_gen_premises.json', "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Premissas salvas em {'utils/auto_gen_premises.json'}")


def main():
    premissas = premises_generator(n=20, depth=2)
    save_premises_to_json(premissas)

if __name__ == "__main__":
    main()
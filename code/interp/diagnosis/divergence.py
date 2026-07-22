import re

def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())

def first_divergence(actions: list, solution: list):
    # First 1-based step where the executed action leaves the exact solution command list;
    # None if every compared step matches (tw-coin validation anchor, decisions section 66)
    for step, (action, command) in enumerate(zip(actions, solution), start=1):
        if normalize(action) != normalize(command):
            return step, normalize(command)
    return None

def corrective_matches(text, command: str) -> bool:
    # Mechanical check: the proposed fix names the solution command (token-contiguous containment)
    return text is not None and normalize(command) in normalize(text)

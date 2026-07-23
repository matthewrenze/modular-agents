import re
from interp.plan.action_matcher import normalize

def parse_inventory(text: str) -> set:
    # "You are carrying: a knife, a white onion and a yellow apple." -> normalized item names
    text = str(text).strip()
    if ":" not in text:
        return set()
    items_text = text.split(":", 1)[1].strip().rstrip(".")
    items = re.split(r",|\band\b", items_text)
    return {normalize(item) for item in items if normalize(item)}

import re
from functools import lru_cache
from typing import Optional

# Filler tokens: articles, prepositions, and TextWorld object-state adjectives
DROPPED = {"the", "a", "an",
           "with", "on", "in", "from", "to", "into", "onto", "using", "back",
           "raw", "diced", "sliced", "chopped", "fried", "roasted", "grilled", "cooked", "prepared"}

# Game-synonym verbs: movement verbs all execute as "go"; grill/fry/roast execute as "cook"
VERB_MAP = {"move": "go", "walk": "go", "head": "go", "travel": "go", "run": "go",
            "explore": "go", "venture": "go",
            "grill": "cook", "fry": "cook", "roast": "cook",
            "insert": "put", "read": "examine"}

@lru_cache(maxsize=100_000)
def normalize(text: str) -> str:
    # Lowercase, drop punctuation, map game-synonym verbs, drop filler tokens, collapse whitespace
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    tokens = (VERB_MAP.get(token, token) for token in text.split())
    return " ".join(token for token in tokens if token not in DROPPED)

class ActionMatcher:

    def match(self, action: str, item_text: str) -> Optional[str]:
        action, item = normalize(action), normalize(item_text)
        if not action or not item:
            return None
        if action == item:
            return "exact"
        if self.contains(item.split(), action.split()) or self.contains(action.split(), item.split()):
            return "fuzzy"
        return None

    def contains(self, tokens: list, sub_tokens: list) -> bool:
        # True if sub_tokens appear as a contiguous run within tokens
        n = len(sub_tokens)
        return any(tokens[i:i + n] == sub_tokens for i in range(len(tokens) - n + 1))

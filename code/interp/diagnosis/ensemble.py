from collections import Counter
from statsmodels.stats import inter_rater

def majority(votes: list):
    # >=2 agreement is ground truth; a null majority means "not localizable" (no ground truth)
    value, count = Counter(votes).most_common(1)[0]
    return value if count >= 2 else None

def step_window(steps: list):
    # Dynamic-tolerance window = [min, max] of the labelers' non-null steps
    named = [step for step in steps if step is not None]
    return (min(named), max(named)) if named else None

def pairwise_rate(first: list, second: list) -> float:
    return sum(a == b for a, b in zip(first, second)) / len(first)

def fleiss_kappa(vote_rows: list) -> float:
    # Rows = episodes, columns = raters; nulls become their own category
    table, _ = inter_rater.aggregate_raters([[str(vote) for vote in row] for row in vote_rows])
    return inter_rater.fleiss_kappa(table)

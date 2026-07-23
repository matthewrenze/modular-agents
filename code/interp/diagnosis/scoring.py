from collections import Counter, defaultdict

def score_class(primary, secondary, truth) -> dict:
    # Strict headline = primary match; lenient sensitivity = primary or secondary (protocol section 10)
    return {"strict": primary == truth, "lenient": truth in (primary, secondary)}

def score_step(judge_step, truth_step, window) -> dict:
    # Three pre-registered variants: exact, fixed +/-2, dynamic labeler-spread window
    return {"step_exact": judge_step is not None and judge_step == truth_step,
            "step_window2": judge_step is not None and abs(judge_step - truth_step) <= 2,
            "step_dynamic": judge_step is not None and window is not None
                            and window[0] <= judge_step <= window[1]}

def cohens_kappa(predictions: list, truths: list) -> float:
    total = len(predictions)
    observed = sum(p == t for p, t in zip(predictions, truths)) / total
    predicted_counts, truth_counts = Counter(predictions), Counter(truths)
    expected = sum(predicted_counts[label] * truth_counts[label]
                   for label in set(predicted_counts) | set(truth_counts)) / total ** 2
    return (observed - expected) / (1 - expected)

def chance_floors(labels: list, families: list) -> dict:
    # Guessing floors conditioned on the grouping: modal-class rate and distribution-matched random
    by_family = defaultdict(list)
    for label, family in zip(labels, families):
        by_family[family].append(label)
    majority_hits = matched_hits = 0.0
    for family_labels in by_family.values():
        counts = Counter(family_labels)
        size = len(family_labels)
        majority_hits += max(counts.values())
        matched_hits += size * sum((count / size) ** 2 for count in counts.values())
    return {"majority": majority_hits / len(labels), "matched_random": matched_hits / len(labels)}

def brier_score(confidences: list, corrects: list) -> float:
    return sum((confidence - correct) ** 2
               for confidence, correct in zip(confidences, corrects)) / len(confidences)

def reliability_bins(confidences: list, corrects: list, n_bins: int = 5) -> list:
    rows = []
    for bin_id in range(n_bins):
        low, high = bin_id / n_bins, (bin_id + 1) / n_bins
        members = [(confidence, correct) for confidence, correct in zip(confidences, corrects)
                   if low <= confidence < high or (bin_id == n_bins - 1 and confidence == 1.0)]
        if members:
            rows.append({"low": low, "high": high, "n": len(members),
                         "mean_confidence": sum(m[0] for m in members) / len(members),
                         "accuracy": sum(m[1] for m in members) / len(members)})
    return rows

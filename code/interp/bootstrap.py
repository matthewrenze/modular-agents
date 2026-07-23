import numpy as np

def micro_rate_ci(numerators, denominators, rng, samples: int = 2000) -> tuple:
    # Micro-averaged rate with a clustered bootstrap CI (episodes resampled with replacement)
    numerators, denominators = np.asarray(numerators), np.asarray(denominators)
    total = denominators.sum()
    if total == 0:
        return np.nan, np.nan, np.nan
    rate = numerators.sum() / total
    resampled = []
    for _ in range(samples):
        index = rng.integers(0, len(numerators), len(numerators))
        denominator = denominators[index].sum()
        if denominator:
            resampled.append(numerators[index].sum() / denominator)
    low, high = np.percentile(resampled, [2.5, 97.5])
    return rate, low, high

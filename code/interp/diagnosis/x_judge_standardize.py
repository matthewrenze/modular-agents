import pandas as pd

# Is the modular-react gap driven by failure-mode mix? (protocol section 11 anticipates this)
results = pd.read_csv("../data/interp/diagnosis/judge-accuracy.csv")
pure = results[results.condition == "pure"]

lines = ["=== Failure-mode mix vs accuracy (pure condition) ===", ""]
table = []
for mode in sorted(pure.ground_truth.unique()):
    row = {"mode": mode}
    for arch, tag in [("modular-full", "mod"), ("react-kn", "rea")]:
        subset = pure[(pure.agent_name == arch) & (pure.ground_truth == mode)]
        row[f"{tag}_n"] = len(subset)
        row[f"{tag}_acc"] = round(subset.strict.mean(), 3) if len(subset) else None
    table.append(row)
frame = pd.DataFrame(table)
lines.append(frame.to_string(index=False))

# Direct standardization: apply each architecture's class mix to the other's per-class accuracy
def standardize(source_arch, weight_arch):
    source = pure[pure.agent_name == source_arch]
    weights = pure[pure.agent_name == weight_arch].ground_truth.value_counts(normalize=True)
    total_weight = accuracy = 0.0
    for mode, weight in weights.items():
        subset = source[source.ground_truth == mode]
        if len(subset) == 0:
            continue  # class absent in the source architecture; renormalize over shared classes
        accuracy += weight * subset.strict.mean()
        total_weight += weight
    return accuracy / total_weight, total_weight

lines += ["", "=== Direct standardization (shared classes only) ==="]
for source, weights in [("modular-full", "react-kn"), ("react-kn", "modular-full")]:
    value, covered = standardize(source, weights)
    lines.append(f"{source} accuracy under {weights}'s class mix: {value:.3f} "
                 f"(covers {covered:.1%} of the weighting mix)")

for arch in ["modular-full", "react-kn"]:
    subset = pure[pure.agent_name == arch]
    lines.append(f"{arch} raw marginal: {subset.strict.mean():.3f}")

# Restrict to classes well-populated in BOTH architectures (>= 5 observations each)
shared = []
for mode in pure.ground_truth.unique():
    mod = pure[(pure.agent_name == "modular-full") & (pure.ground_truth == mode)]
    rea = pure[(pure.agent_name == "react-kn") & (pure.ground_truth == mode)]
    if len(mod) >= 5 and len(rea) >= 5:
        shared.append(mode)
lines += ["", f"=== Restricted to classes with >=5 obs in both ({len(shared)} classes: {sorted(shared)}) ==="]
for arch in ["modular-full", "react-kn"]:
    subset = pure[(pure.agent_name == arch) & (pure.ground_truth.isin(shared))]
    lines.append(f"{arch}: {subset.strict.mean():.3f} ({subset.strict.sum()}/{len(subset)})")

# Modular-exclusive classes: how much do they cost the marginal?
excluded = [m for m in pure.ground_truth.unique() if m not in shared]
lines += ["", f"=== Classes NOT shared ({excluded}) ==="]
for arch in ["modular-full", "react-kn"]:
    subset = pure[(pure.agent_name == arch) & (pure.ground_truth.isin(excluded))]
    if len(subset):
        lines.append(f"{arch}: {subset.strict.mean():.3f} ({subset.strict.sum()}/{len(subset)}) "
                     f"= {len(subset) / len(pure[pure.agent_name == arch]):.1%} of its observations")

report = "\n".join(lines)
with open("../data/interp/diagnosis/judge-standardization.txt", "w", encoding="utf-8") as f:
    f.write(report + "\n")
print(report)

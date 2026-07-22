# Scratch: verify the E1 prompt's frozen text is character-identical to run_judge.py's (D1/C2)
# frozen instruction text — taxonomy bullets, root-cause-step, faulty-module, confidence,
# corrective-action, and evidence bullets (decisions section 79 pattern).
import os

HERE = os.path.dirname(__file__)

def read(name):
    with open(os.path.join(HERE, name), "r", encoding="utf-8") as f:
        return f.read()

def between(text, start, end):
    i = text.find(start)
    j = text.find(end, i)
    assert i != -1 and j != -1, f"markers not found: {start[:40]!r}"
    return text[i:j + len(end)]

judge = read("run_judge.py")
agentic = read("agentic.py")

checks = [
    ("primary-cause + taxonomy + root_cause_step block",
     "- The primary cause is the single most decisive",
     "cannot be tied to any step.\n"),
    ("faulty_module modular bullet",
     "- `faulty_module`: the module that committed",
     "no single module can be identified.\""),
    ("faulty_module react bullet",
     "- `faulty_module`: always null",
     "no module decomposition.\""),
    ("corrective_action bullet",
     "- `corrective_action`: one line",
     "should have been executed).\n"),
    ("evidence bullet",
     "- Cite evidence as specific step numbers",
     "what each shows.\n"),
]

all_ok = True
for label, start, end in checks:
    a, b = between(judge, start, end), between(agentic, start, end)
    ok = a == b
    all_ok &= ok
    print(f"{'OK  ' if ok else 'DIFF'} {label}")
    if not ok:
        for k, (ca, cb) in enumerate(zip(a, b)):
            if ca != cb:
                print(f"     first diff at char {k}: {a[max(0,k-40):k+40]!r} vs {b[max(0,k-40):k+40]!r}")
                break
        if len(a) != len(b):
            print(f"     lengths differ: {len(a)} vs {len(b)}")

# The confidence bullet differs by design only in the dash? It must not — check it verbatim too.
conf_judge = between(judge, "- `confidence`:", "is correct.")
conf_agentic = between(agentic, "- `confidence`:", "is correct.")
ok = conf_judge == conf_agentic
all_ok &= ok
print(f"{'OK  ' if ok else 'DIFF'} confidence bullet")
if not ok:
    print(f"     {conf_judge!r}\n  vs {conf_agentic!r}")

print("ALL FROZEN TEXT IDENTICAL" if all_ok else "FROZEN TEXT DRIFT — FIX BEFORE SWEEP")

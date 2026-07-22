# Scratch: verify importing the agentic driver executes nothing (no sweep on import).
import interp.diagnosis.run_agentic_judge  # noqa: F401 — the import IS the test
print("import OK — no sweep executed")

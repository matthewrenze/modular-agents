import json
import pandas as pd
from interp.episode_extract import EpisodeExtract
from interp.diagnosis.bundles import truncate, FIELD_CAP, FINAL_CAP
from interp.diagnosis.record import ExtendedRecordParser, extract_json

MODULAR_TOOLS = ["read_summaries", "read_thoughts", "read_actions", "read_observations",
                 "read_plan_updates", "read_memory_updates", "read_plan", "read_memories", "read_steps"]
REACT_TOOLS = ["read_thoughts", "read_actions", "read_observations", "read_steps"]

RANGE_KEYS = {"read_summaries": ("summary", "summary"), "read_thoughts": ("thought", "thought"),
              "read_actions": ("action", "action"), "read_observations": ("feedback", "observation")}

FORMAT_REMINDER_AGENTIC = """Your previous response could not be parsed. Respond with ONLY a JSON object in one of these two forms.
To read more of the record (up to 6 reads per turn; "from"/"to" are optional step numbers):
{ "reads": [ { "tool": "<tool name>", "from": <step>, "to": <step> }, ... ] }
To end the audit with your diagnosis, with "primary_cause" chosen from the fixed taxonomy slugs listed in the instructions:
{ "diagnose": { "primary_cause": "<slug>", "secondary_cause": "<slug or null>",
  "root_cause_step": <integer or null>, "faulty_module": "<module or null>",
  "confidence": <0.0-1.0>, "corrective_action": "<one line>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] } }"""

BUDGET_MESSAGE = """Retrieval budget exhausted: no further reads are allowed. Respond now with ONLY your diagnosis JSON: { "diagnose": { ... } }"""

# --- E1 intro prompt (frozen at the 4.2 checkpoint gate) ---------------------------------------
# The diagnosis-instruction text below is copied verbatim from run_judge.py's frozen D1/C2 text
# (verified character-identical by x_agentic_prompt_check.py); only the head, tools, and protocol
# sections are new, and the response format wraps the same record in {"diagnose": ...}.

HEAD_MODULAR = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You investigate interactively: the episode record sits behind read tools, and you request exactly the parts you want to read. The agent is a modular agent — at every step a summarizer wrote a summary of what just happened, a memorizer maintained a persistent memory store, a planner maintained a persistent plan, a reasoner wrote a thought choosing the next move, and an actor emitted the action. You may read everything the agent wrote and the game's response text, but you do NOT see the game's internal state, the score, or the correct solution."""

HEAD_REACT = """You are a failure diagnostician auditing an LLM agent that played a text-based game (TextWorld) and FAILED its task. You investigate interactively: the episode record sits behind read tools, and you request exactly the parts you want to read. The agent is a ReAct agent — at every step it wrote a thought choosing its next move and emitted the action; it keeps no plan, memory, or summary artifacts. You may read everything the agent wrote and the game's response text, but you do NOT see the game's internal state, the score, or the correct solution."""

TOOLS_DOC_COMMON = """- read_thoughts(from, to) — the agent's per-step thoughts
- read_actions(from, to) — the agent's per-step executed actions
- read_observations(from, to) — the game's response text as the agent saw it each step (the observation at step N is the game's response to the action at step N-1; when "to" reaches the final step, the game's response to the last action is included)
- read_steps(from, to) — per-step interleaved records: observation, thought, action"""

TOOLS_DOC_MODULAR = """- read_summaries(from, to) — the agent's per-step summaries (its running account of what happened)
""" + TOOLS_DOC_COMMON + """
- read_plan_updates(from, to) — the full plan snapshot at each step in the range where the plan changed
- read_memory_updates(from, to) — the full memory snapshot at each step in the range where the memory changed
- read_plan() — the final plan as the episode ended
- read_memories() — the final memory store as the episode ended"""

PROTOCOL_SECTION = """

=== PROTOCOL ===
Every response must be ONLY a JSON object, in one of two forms.
1. A read request — up to 6 reads per turn:
{ "reads": [ { "tool": "read_actions" }, { "tool": "read_thoughts", "from": 10, "to": 20 } ] }
2. Your final diagnosis, when you are confident (this ends the audit; no reads afterward):
{ "diagnose": { ... } } — the full form is specified below.
You have at most 40 read turns. Your retrieval is metered: read what you need to reach a confident diagnosis, but no more.

=== DIAGNOSIS INSTRUCTIONS ===
"""

INSTRUCTIONS_TOP = """- The primary cause is the single most decisive reason this episode failed — the thing that, had it gone right, would most likely have flipped the outcome. Hitting the step limit is an outcome, not automatically a cause: ask WHY the agent did not finish in time.
- Choose `primary_cause` from this fixed taxonomy (use the slug exactly):
  - position-miscount-skip — Miscounted its position in the prescribed sequence (e.g. off-by-one, or conflating step count with move count) and executed a later instruction early, skipping one that was never performed
  - extra-move-insertion — Inserted a move the route does not contain — re-executing the just-completed instruction or extending a repeated run of identical moves by one
  - direction-misread — At the correct sequence position, misread the next instruction's direction and executed a different, substituted direction not in the route
  - lost-place-reanchor — Lost its place in the route text and re-anchored on a similar phrase elsewhere, jumping forward or rewinding to replay a block of instructions
  - route-copy-corruption — The agent's stored copy of the route was corrupted — instructions dropped, duplicated, or altered during transcription, replanning, or updates — and the agent faithfully executed the corrupted copy
  - checklist-overtick-skip — The agent's progress tracking marked route items as done that were never executed, so the following move(s) were skipped
  - intent-action-mismatch — The agent's stated intended move and its emitted command differ; the executed action contradicts the reasoning that chose it
  - cooking-recipe-errors — Recipe execution errors: misordered steps, wrong appliance, wrong cut, or misremembered recipe details
  - capacity-misbelief-loop — Falsely assumed an inventory-capacity limit blocked progress, causing futile item swapping or perceived deadlock
  - failed-move-desync — Advanced or failed to advance the route pointer correctly after failed or blocked movement attempts
  - hallucinated-state-quit — Hallucinated completion, success, or execution that never happened, causing premature quitting or skipped instructions
  - malformed-action-output — The agent emitted malformed output — meta-text, JSON, corrupted or duplicated command strings — instead of valid commands
  - abandoned-prescribed-route — Abandoned, truncated, or prematurely declared the prescribed route complete, often switching to exploration
  - other — Escape class: no listed class fits (also holds genuine one-off causes)
- Pick `other` only if no listed class fits. If two classes fit, the more specific one is `primary_cause` and the broader one is `secondary_cause`; otherwise `secondary_cause` is a second contributing slug or null.
- `root_cause_step`: the first step number at which the record shows the agent deviating from a path that could still have succeeded — for a specific slip, the step of the slip; for gradual drift, the first step where the agent is observably off the correct path. Use null ONLY if the failure cannot be tied to any step.
"""

FAULTY_MODULE_BULLET_MODULAR = "- `faulty_module`: the module that committed the root-cause error — `summarizer`, `memorizer`, `planner`, `reasoner`, or `actor`. Attribute the module that ORIGINATED the error, not the modules that propagated it. Use null only if no single module can be identified."

FAULTY_MODULE_BULLET_REACT = "- `faulty_module`: always null — this agent has no module decomposition."

INSTRUCTIONS_BOTTOM = """
- `confidence`: your subjective probability, 0.0–1.0, that your `primary_cause` is correct.
- `corrective_action`: one line — the single concrete change at the root-cause step that would most likely have flipped the outcome (for example, the exact command that should have been executed).
- Cite evidence as specific step numbers with a few words on what each shows.

When you are ready to diagnose, respond with ONLY:
{ "diagnose": { "primary_cause": "<slug>", "secondary_cause": "<slug or null>",
  "root_cause_step": <integer or null>, "faulty_module": "<module or null>",
  "confidence": <0.0-1.0>, "corrective_action": "<one line>",
  "rationale": "<2-5 sentences>", "evidence": ["step N: <what it shows>", "..."] } }

Begin your audit now with your first read request."""

def build_intro(task: str, n_steps: int, is_modular: bool) -> str:
    head = HEAD_MODULAR if is_modular else HEAD_REACT
    tools_doc = TOOLS_DOC_MODULAR if is_modular else TOOLS_DOC_COMMON
    module_bullet = FAULTY_MODULE_BULLET_MODULAR if is_modular else FAULTY_MODULE_BULLET_REACT
    return (head
            + f"\n\n=== TASK ===\n{task}\n\nThe episode ran {n_steps} steps and ended in failure.\n\n=== TOOLS ===\n"
            + f'Steps are numbered 1-{n_steps}. "from"/"to" are optional and default to the full episode.\n'
            + tools_doc + PROTOCOL_SECTION + INSTRUCTIONS_TOP + module_bullet + INSTRUCTIONS_BOTTOM)

def cell(row: dict, key: str) -> str:
    value = row.get(key, "")
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    return str(value).strip()

class ActionParser:
    """Parses one judge turn into a read request or a diagnosis (protocol E1)."""

    def __init__(self):
        self.record_parser = ExtendedRecordParser()

    def parse(self, response: str) -> dict:
        data = extract_json(response)
        if data is None:
            return None
        if "diagnose" in data:
            if not isinstance(data["diagnose"], dict):
                return None
            record = self.record_parser.parse(json.dumps(data["diagnose"]))
            if record is None:
                return None
            return {"type": "diagnose", "record": record}
        reads = data.get("reads")
        if not isinstance(reads, list) or not reads:
            return None
        parsed = []
        for read in reads:
            if not isinstance(read, dict) or not isinstance(read.get("tool"), str):
                return None
            parsed.append({"tool": read["tool"].strip(),
                           "from": self._parse_step(read.get("from")), "to": self._parse_step(read.get("to"))})
        return {"type": "reads", "reads": parsed}

    def _parse_step(self, value) -> int:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, str) and value.strip().isdigit():
            return int(value.strip())
        return None

class RetrievalTools:
    """Executes read requests over one episode and meters the retrieved chars per channel.
    total_chars counts the full returned text (what the judge reads); channel_chars counts
    rendered field content only (for channel attribution)."""

    def __init__(self, extract: EpisodeExtract, is_modular: bool):
        self.tools = MODULAR_TOOLS if is_modular else REACT_TOOLS
        self.rows = extract.details.to_dict("records")
        self.n_steps = len(self.rows)
        self.terminal_feedback = str(extract.state.step_history[-1].env_state.feedback or "").strip()
        self.final_plan = extract.state.plan
        self.final_memories = "\n".join(f"{key}: {value}" for key, value in extract.state.memories.items())
        self.plan_updates, self.memory_updates = [], []
        prev_plan, prev_memory = "", ""
        for step in extract.state.step_history[:-1]:
            agent_state = step.agent_state
            if agent_state.plan and agent_state.plan != prev_plan:
                self.plan_updates.append((step.step_id, agent_state.plan))
            if agent_state.memory and agent_state.memory != prev_memory:
                self.memory_updates.append((step.step_id, agent_state.memory))
            prev_plan, prev_memory = agent_state.plan, agent_state.memory
        self.calls = []
        self.total_chars = 0
        self.channel_chars = {}

    def execute(self, tool: str, from_: int = None, to: int = None) -> str:
        if tool not in self.tools:
            text = (f"[{tool}] ERROR: unknown tool for this episode. "
                    f"Available tools: {', '.join(self.tools)}.")
            return self._account(tool, from_, to, text, {})
        if tool == "read_plan":
            return self._final(tool, "final_plan", self.final_plan)
        if tool == "read_memories":
            return self._final(tool, "final_memories", self.final_memories)
        lo = 1 if from_ is None else max(1, from_)
        hi = self.n_steps if to is None else min(self.n_steps, to)
        if lo > hi:
            text = f"[{tool}] ERROR: empty step range."
            return self._account(tool, from_, to, text, {})
        if tool in RANGE_KEYS:
            return self._range_channel(tool, lo, hi)
        if tool in ("read_plan_updates", "read_memory_updates"):
            return self._updates(tool, lo, hi)
        return self._steps(lo, hi)

    def _final(self, tool: str, channel: str, content: str) -> str:
        body = truncate(content, FINAL_CAP) if content.strip() else "(empty)"
        text = f"[{tool}]\n{body}"
        return self._account(tool, None, None, text, {channel: len(body) if content.strip() else 0})

    def _range_channel(self, tool: str, lo: int, hi: int) -> str:
        key, channel = RANGE_KEYS[tool]
        lines, content_chars = [f"[{tool} steps {lo}-{hi}]"], 0
        for row in self.rows[lo - 1:hi]:
            content = truncate(cell(row, key), FIELD_CAP)
            content_chars += len(content)
            lines.append(f"Step {row['step_id']}: {content or '(empty)'}")
        if tool == "read_observations" and hi == self.n_steps and self.terminal_feedback:
            terminal = truncate(self.terminal_feedback, FIELD_CAP)
            content_chars += len(terminal)
            lines.append(f"Episode end (after step {self.n_steps}): {terminal}")
        return self._account(tool, lo, hi, "\n".join(lines), {channel: content_chars})

    def _updates(self, tool: str, lo: int, hi: int) -> str:
        updates = self.plan_updates if tool == "read_plan_updates" else self.memory_updates
        label, noun = ("Plan", "plan") if tool == "read_plan_updates" else ("Memory", "memory")
        channel = "plan_update" if tool == "read_plan_updates" else "memory_update"
        in_range = [(step_id, content) for step_id, content in updates if lo <= step_id <= hi]
        if not in_range:
            before = [step_id for step_id, _ in updates if step_id < lo]
            hint = (f"The {noun} last changed at step {before[-1]}." if before
                    else f"The {noun} did not change before this range.")
            text = f"[{tool} steps {lo}-{hi}]\nNo {noun} changes in steps {lo}-{hi}. {hint}"
            return self._account(tool, lo, hi, text, {})
        blocks, content_chars = [f"[{tool} steps {lo}-{hi}]"], 0
        for step_id, content in in_range:
            snapshot = truncate(content, FIELD_CAP)
            content_chars += len(snapshot)
            blocks.append(f"--- {label} as of step {step_id} ---\n{snapshot}")
        return self._account(tool, lo, hi, "\n".join(blocks), {channel: content_chars})

    def _steps(self, lo: int, hi: int) -> str:
        blocks = [f"[read_steps steps {lo}-{hi}]"]
        channels = {"observation": 0, "thought": 0, "action": 0}
        for row in self.rows[lo - 1:hi]:
            lines = [f"--- Step {row['step_id']} ---"]
            observation = truncate(cell(row, "feedback"), FIELD_CAP)
            if observation:
                channels["observation"] += len(observation)
                lines.append(f"Observation: {observation}")
            thought = truncate(cell(row, "thought"), FIELD_CAP)
            if thought:
                channels["thought"] += len(thought)
                lines.append(f"Thought: {thought}")
            action = truncate(cell(row, "action"), FIELD_CAP)
            channels["action"] += len(action)
            lines.append(f"Action: {action}")
            blocks.append("\n".join(lines))
        if hi == self.n_steps and self.terminal_feedback:
            terminal = truncate(self.terminal_feedback, FIELD_CAP)
            channels["observation"] += len(terminal)
            blocks.append(f"--- Episode end (after step {self.n_steps}) ---\nObservation: {terminal}")
        return self._account("read_steps", lo, hi, "\n".join(blocks), channels)

    def _account(self, tool: str, lo: int, hi: int, text: str, channels: dict) -> str:
        self.calls.append({"tool": tool, "from": lo, "to": hi, "chars": len(text)})
        self.total_chars += len(text)
        for channel, chars in channels.items():
            self.channel_chars[channel] = self.channel_chars.get(channel, 0) + chars
        return text

class AgenticSession:
    """Runs one episode's multi-turn read-and-diagnose loop with one judge model."""

    def __init__(self, model, tools: RetrievalTools, parser: ActionParser, intro: str,
                 max_read_turns: int = 40, max_reads_per_turn: int = 6):
        self.model = model
        self.tools = tools
        self.parser = parser
        self.intro = intro
        self.max_read_turns = max_read_turns
        self.max_reads_per_turn = max_reads_per_turn

    def run(self) -> dict:
        messages = [{"role": "user", "content": self.intro}]
        turn_tokens = []
        record, outcome = None, None
        read_turns, strikes = 0, 0
        while True:
            self.model.reset_step()
            response = self.model.get_response(messages)
            turn_tokens.append({"cached": self.model.step_cached_tokens, "input": self.model.step_input_tokens,
                                "reasoning": self.model.step_reasoning_tokens, "output": self.model.step_output_tokens})
            messages.append({"role": "assistant", "content": response})
            parsed = self.parser.parse(response)
            if parsed is None:
                strikes += 1
                if strikes >= 2:
                    outcome = "malformed"
                    break
                messages.append({"role": "user", "content": FORMAT_REMINDER_AGENTIC})
                continue
            if parsed["type"] == "diagnose":
                record, outcome = parsed["record"], "diagnosed"
                break
            reads = parsed["reads"]
            if len(reads) > self.max_reads_per_turn:
                strikes += 1
                if strikes >= 2:
                    outcome = "malformed"
                    break
                messages.append({"role": "user", "content":
                                 f"Too many reads in one turn: at most {self.max_reads_per_turn} are allowed. "
                                 f"Re-send a smaller request."})
                continue
            if read_turns >= self.max_read_turns:
                strikes += 1
                if strikes >= 2:
                    outcome = "budget-exhausted"
                    break
                messages.append({"role": "user", "content": BUDGET_MESSAGE})
                continue
            strikes = 0
            results = [self.tools.execute(read["tool"], read["from"], read["to"]) for read in reads]
            read_turns += 1
            messages.append({"role": "user", "content": "\n\n".join(results)})
        return {"record": record, "outcome": outcome, "read_turns": read_turns,
                "n_turns": len(turn_tokens), "turn_tokens": turn_tokens, "messages": messages}

import pandas as pd
from params.parameters import Parameters
from states.global_state import GlobalState
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState
from interp.episode_extract import EpisodeExtract
from interp.diagnosis.bundles import LabelerBundleRenderer, truncate

OUTCOME = {"success": False, "score": 0, "max_score": 1, "steps": 75, "max_steps": 75, "max_steps_hit": True}

def make_step(step_id, feedback="", location="Kitchen", inventory="You are carrying nothing.", score=0,
              is_done=False, summary="", plan="", memory="", thought="", action=""):
    env_state = EnvState(feedback=feedback, location=location, inventory=inventory, score=score, is_done=is_done)
    agent_state = AgentState(summary=summary, plan=plan, memory=memory, thought=thought, action=action)
    return StepState(step_id=step_id, env_state=env_state, agent_state=agent_state)

def make_extract(agent_name="modular-full", plan="", memories=None, steps=None, last_messages=None):
    params = Parameters(version="v6.0", split_name="test", model_name="gpt-5.5",
                        agent_name=agent_name, eval_name="tw-coin-1", episode_id=50)
    task_state = TaskState(task="Find the coin.", max_steps=75, max_score=1)
    state = GlobalState(task_state=task_state, plan=plan, memories=memories or {},
                        step_history=steps or [make_step(1), make_step(2, is_done=True)])
    return EpisodeExtract(params=params, state=state, details=pd.DataFrame(), last_messages=last_messages or {})

class TestLabelerBundleRenderer:

    def test_renders_header_with_outcome_stats(self):
        bundle = LabelerBundleRenderer().render(make_extract(), ["go north"], OUTCOME)
        assert "Model: gpt-5.5" in bundle
        assert "Agent: modular-full" in bundle
        assert "Eval: tw-coin-1 (episode 50)" in bundle
        assert "success = False, score = 0/1, steps = 75/75, max_steps_hit = True" in bundle

    def test_renders_task_and_solution(self):
        bundle = LabelerBundleRenderer().render(make_extract(), ["go north", "take coin"], OUTCOME)
        assert "=== TASK ===\nFind the coin." in bundle
        assert "=== GROUND-TRUTH SOLUTION ===\ngo north, take coin" in bundle

    def test_renders_final_plan_and_memories_when_present(self):
        extract = make_extract(plan="- [ ] Go north", memories={"kitchen": "rooms = {north = closet}"})
        bundle = LabelerBundleRenderer().render(extract, ["go north"], OUTCOME)
        assert "=== FINAL PLAN ===\n- [ ] Go north" in bundle
        assert "=== FINAL MEMORIES ===\nkitchen: rooms = {north = closet}" in bundle

    def test_skips_final_plan_and_memories_when_absent(self):
        extract = make_extract(agent_name="react-kn")
        bundle = LabelerBundleRenderer().render(extract, ["go north"], OUTCOME)
        assert "=== FINAL PLAN ===" not in bundle
        assert "=== FINAL MEMORIES ===" not in bundle

    def test_renders_acted_step_env_and_agent_fields(self):
        steps = [make_step(1, location="Scullery", score=1, summary="start", thought="Go north first.",
                           action="go north"),
                 make_step(2, feedback="You entered a basement.", is_done=True)]
        bundle = LabelerBundleRenderer().render(make_extract(steps=steps), ["go north"], OUTCOME)
        assert "--- Step 1 ---" in bundle
        assert "Location: Scullery" in bundle
        assert "Inventory: You are carrying nothing." in bundle
        assert "Score: 1" in bundle
        assert "Summary: start" in bundle
        assert "Thought: Go north first." in bundle
        assert "Action: go north" in bundle

    def test_renders_terminal_entry_as_episode_outcome(self):
        steps = [make_step(1, action="go north"),
                 make_step(2, feedback="You entered a basement.", is_done=True, action="never shown")]
        bundle = LabelerBundleRenderer().render(make_extract(steps=steps), ["go north"], OUTCOME)
        assert "--- Episode outcome ---\nFeedback: You entered a basement.\nDone: True" in bundle
        assert "--- Step 2 ---" not in bundle
        assert "never shown" not in bundle

    def test_renders_plan_and_memory_only_when_changed(self):
        steps = [make_step(1, plan="- [ ] A", memory="m1", action="go north"),
                 make_step(2, plan="- [ ] A", memory="m1", action="go west"),
                 make_step(3, plan="- [x] A", memory="m2", action="go south"),
                 make_step(4, is_done=True)]
        bundle = LabelerBundleRenderer().render(make_extract(steps=steps), ["go north"], OUTCOME)
        assert bundle.count("Plan:\n- [ ] A") == 1
        assert bundle.count("Plan:\n- [x] A") == 1
        assert bundle.count("Memory:\nm1") == 1
        assert bundle.count("Memory:\nm2") == 1

    def test_omits_empty_fields(self):
        steps = [make_step(1, action="go north"), make_step(2, is_done=True)]
        bundle = LabelerBundleRenderer().render(make_extract(agent_name="react-kn", steps=steps),
                                                ["go north"], OUTCOME)
        assert "Summary:" not in bundle
        assert "Plan:" not in bundle
        assert "Memory:" not in bundle
        assert "Thought:" not in bundle
        assert "Feedback:" not in bundle.split("--- Episode outcome ---")[0]

    def test_renders_last_messages_in_module_order(self):
        last_messages = {75: {"actor": "ACTOR 75", "summarizer": "SUMMARIZER 75"}, 74: {"actor": "ACTOR 74"}}
        bundle = LabelerBundleRenderer().render(make_extract(last_messages=last_messages), ["go north"], OUTCOME)
        assert "=== RAW MODULE MESSAGES (LAST 2 STEPS) ===" in bundle
        assert "--- Step 74 - actor ---\nACTOR 74" in bundle
        assert bundle.index("--- Step 74 - actor ---") < bundle.index("--- Step 75 - summarizer ---")
        assert bundle.index("--- Step 75 - summarizer ---") < bundle.index("--- Step 75 - actor ---")

class TestTruncate:

    def test_returns_short_text_unchanged(self):
        assert truncate("short text", 4000) == "short text"

    def test_truncates_head_and_tail_with_marker(self):
        text = "H" * 600 + "M" * 800 + "T" * 600
        result = truncate(text, 1000)
        assert result.startswith("H" * 500)
        assert result.endswith("T" * 500)
        assert "[... truncated 1000 chars ...]" in result

class TestLabelerBundleRendererCaps:

    def test_caps_step_fields(self):
        steps = [make_step(1, summary="s" * 5000, thought="t" * 5000, action="a" * 5000,
                           plan="p" * 5000, memory="m" * 5000),
                 make_step(2, is_done=True)]
        bundle = LabelerBundleRenderer().render(make_extract(steps=steps), ["go north"], OUTCOME)
        assert "s" * 4001 not in bundle
        assert "t" * 4001 not in bundle
        assert "a" * 4001 not in bundle
        assert "p" * 4001 not in bundle
        assert "m" * 4001 not in bundle
        assert bundle.count("[... truncated 1000 chars ...]") == 5

    def test_caps_final_plan_and_memories(self):
        extract = make_extract(plan="p" * 40000, memories={"kitchen": "v" * 40000})
        bundle = LabelerBundleRenderer().render(extract, ["go north"], OUTCOME)
        assert "p" * 30001 not in bundle
        assert "v" * 30001 not in bundle
        assert bundle.count("truncated") == 2

    def test_caps_raw_messages(self):
        last_messages = {75: {"actor": "x" * 40000}}
        bundle = LabelerBundleRenderer().render(make_extract(last_messages=last_messages), ["go north"], OUTCOME)
        assert "x" * 30001 not in bundle
        assert "[... truncated 10000 chars ...]" in bundle

    def test_does_not_cap_fields_at_their_limits(self):
        steps = [make_step(1, thought="t" * 4000), make_step(2, is_done=True)]
        bundle = LabelerBundleRenderer().render(make_extract(steps=steps), ["go north"], OUTCOME)
        assert "t" * 4000 in bundle
        assert "truncated" not in bundle

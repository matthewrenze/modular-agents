import json
import pandas as pd
from params.parameters import Parameters
from states.global_state import GlobalState
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState
from interp.episode_extract import EpisodeExtract
from interp.diagnosis.agentic import (ActionParser, RetrievalTools, AgenticSession,
                                      FORMAT_REMINDER_AGENTIC, BUDGET_MESSAGE, build_intro)

def make_step(step_id, feedback="", location="Kitchen", inventory="", score=0, is_done=False,
              summary="", plan="", memory="", thought="", action=""):
    env_state = EnvState(feedback=feedback, location=location, inventory=inventory, score=score, is_done=is_done)
    agent_state = AgentState(summary=summary, plan=plan, memory=memory, thought=thought, action=action)
    return StepState(step_id=step_id, env_state=env_state, agent_state=agent_state)

def make_extract(agent_name="modular-full", plan="", memories=None, steps=None, details=None):
    params = Parameters(version="v6.0", split_name="test", model_name="gpt-5.5",
                        agent_name=agent_name, eval_name="tw-coin-1", episode_id=50)
    task_state = TaskState(task="Find the coin.", max_steps=75, max_score=1)
    state = GlobalState(task_state=task_state, plan=plan, memories=memories or {},
                        step_history=steps or [make_step(1), make_step(2, is_done=True)])
    if details is None:
        details = pd.DataFrame([{"step_id": 1, "feedback": "", "summary": "", "thought": "", "action": ""}])
    return EpisodeExtract(params=params, state=state, details=details, last_messages={})

def make_three_step_extract(agent_name="modular-full"):
    steps = [make_step(1, feedback="You are in a kitchen.", summary="Started in kitchen",
                       plan="- [ ] Go north", memory="kitchen: start",
                       thought="I should go north.", action="go north"),
             make_step(2, feedback="You entered a closet.", summary="Moved north to closet",
                       plan="- [x] Go north", memory="kitchen: start",
                       thought="Now take the coin.", action="take coin"),
             make_step(3, feedback="You can't see any such thing.", summary="Failed to take coin",
                       plan="- [x] Go north", memory="closet: no coin here",
                       thought="The coin is not here.", action="look"),
             make_step(4, feedback="You lost.", is_done=True)]
    details = pd.DataFrame([
        {"step_id": 1, "feedback": "You are in a kitchen.", "summary": "Started in kitchen",
         "thought": "I should go north.", "action": "go north"},
        {"step_id": 2, "feedback": "You entered a closet.", "summary": "Moved north to closet",
         "thought": "Now take the coin.", "action": "take coin"},
        {"step_id": 3, "feedback": "You can't see any such thing.", "summary": "Failed to take coin",
         "thought": "The coin is not here.", "action": "look"}])
    return make_extract(agent_name=agent_name, plan="- [x] Go north",
                        memories={"closet": "no coin here"}, steps=steps, details=details)

DIAGNOSIS = {"primary_cause": "direction-misread", "secondary_cause": None, "root_cause_step": 2,
             "faulty_module": "reasoner", "confidence": 0.8, "corrective_action": "take coin earlier",
             "rationale": "It looked in the wrong room.", "evidence": ["step 2: wrong move"]}

class TestActionParser:

    def test_parses_read_request_without_range(self):
        parsed = ActionParser().parse('{"reads": [{"tool": "read_summaries"}]}')
        assert parsed == {"type": "reads", "reads": [{"tool": "read_summaries", "from": None, "to": None}]}

    def test_parses_read_request_with_range_and_coerces_string_steps(self):
        parsed = ActionParser().parse('{"reads": [{"tool": "read_thoughts", "from": "10", "to": 20}]}')
        assert parsed["reads"] == [{"tool": "read_thoughts", "from": 10, "to": 20}]

    def test_parses_multiple_reads_in_one_turn(self):
        parsed = ActionParser().parse('{"reads": [{"tool": "read_plan"}, {"tool": "read_memories"}]}')
        assert [read["tool"] for read in parsed["reads"]] == ["read_plan", "read_memories"]

    def test_parses_diagnosis_into_extended_record(self):
        parsed = ActionParser().parse(json.dumps({"diagnose": DIAGNOSIS}))
        assert parsed["type"] == "diagnose"
        assert parsed["record"]["primary_cause"] == "direction-misread"
        assert parsed["record"]["root_cause_step"] == 2

    def test_parses_json_wrapped_in_prose_or_fences(self):
        response = "Here is my request:\n```json\n{\"reads\": [{\"tool\": \"read_actions\"}]}\n```"
        assert ActionParser().parse(response)["type"] == "reads"

    def test_parses_read_request_with_hallucinated_continuation(self):
        # Fable sometimes emits valid JSON then keeps generating a fake dialogue whose braces
        # break first-to-last-brace extraction; the first balanced object is the request
        response = ('{"reads": [{"tool": "read_actions"}]}\n\nuser Step 1: go south\n\n'
                    'assistant {"reads": [{"tool": "read_thoughts", "from": 3}]}')
        parsed = ActionParser().parse(response)
        assert parsed == {"type": "reads", "reads": [{"tool": "read_actions", "from": None, "to": None}]}

    def test_parses_diagnosis_with_trailing_garbage(self):
        response = json.dumps({"diagnose": DIAGNOSIS}) + "\n\nuser Thank you. {done}"
        parsed = ActionParser().parse(response)
        assert parsed["type"] == "diagnose"
        assert parsed["record"]["primary_cause"] == "direction-misread"

    def test_rejects_diagnosis_with_invalid_slug(self):
        bad = dict(DIAGNOSIS, primary_cause="not-a-class")
        assert ActionParser().parse(json.dumps({"diagnose": bad})) is None

    def test_rejects_response_without_json(self):
        assert ActionParser().parse("I would like to read the summaries.") is None

    def test_rejects_empty_or_non_list_reads(self):
        assert ActionParser().parse('{"reads": []}') is None
        assert ActionParser().parse('{"reads": "read_summaries"}') is None

    def test_rejects_read_entry_without_tool(self):
        assert ActionParser().parse('{"reads": [{"from": 1, "to": 5}]}') is None

class TestRetrievalTools:

    def test_read_summaries_returns_numbered_steps(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_summaries")
        assert "[read_summaries steps 1-3]" in result
        assert "Step 1: Started in kitchen" in result
        assert "Step 3: Failed to take coin" in result

    def test_ranges_clamp_to_episode_bounds(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_thoughts", from_=2, to=99)
        assert "Step 1:" not in result
        assert "Step 2: Now take the coin." in result
        assert "Step 3: The coin is not here." in result

    def test_single_step_read_uses_from_equals_to(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_actions", from_=2, to=2)
        assert "Step 2: take coin" in result
        assert "Step 1:" not in result and "Step 3:" not in result

    def test_read_observations_includes_episode_end_when_range_reaches_final_step(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_observations")
        assert "Step 1: You are in a kitchen." in result
        assert "Episode end (after step 3): You lost." in result

    def test_read_observations_excludes_episode_end_when_range_stops_short(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_observations", from_=1, to=2)
        assert "Episode end" not in result

    def test_read_plan_updates_returns_snapshots_only_at_change_steps(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_plan_updates")
        assert "--- Plan as of step 1 ---\n- [ ] Go north" in result
        assert "--- Plan as of step 2 ---\n- [x] Go north" in result
        assert "step 3" not in result

    def test_read_memory_updates_returns_snapshots_only_at_change_steps(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_memory_updates")
        assert "--- Memory as of step 1 ---\nkitchen: start" in result
        assert "--- Memory as of step 3 ---\ncloset: no coin here" in result
        assert "step 2" not in result

    def test_empty_update_range_reports_last_change_step(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_memory_updates", from_=2, to=2)
        assert "No memory changes in steps 2-2" in result
        assert "last changed at step 1" in result

    def test_read_plan_and_read_memories_return_final_artifacts(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        assert "- [x] Go north" in tools.execute("read_plan")
        assert "closet: no coin here" in tools.execute("read_memories")

    def test_read_steps_interleaves_observation_thought_action(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_steps", from_=2, to=2)
        block = "--- Step 2 ---\nObservation: You entered a closet.\nThought: Now take the coin.\nAction: take coin"
        assert block in result

    def test_read_steps_appends_episode_end_observation_at_final_step(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        result = tools.execute("read_steps", from_=3, to=3)
        assert "--- Episode end (after step 3) ---\nObservation: You lost." in result

    def test_react_roster_excludes_artifact_tools(self):
        tools = RetrievalTools(make_three_step_extract(agent_name="react-kn"), is_modular=False)
        result = tools.execute("read_summaries")
        assert "ERROR" in result
        assert "read_thoughts" in result  # error message lists the available tools

    def test_unknown_tool_returns_error_text(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        assert "ERROR" in tools.execute("read_minds")

    def test_empty_range_returns_error_text(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        assert "ERROR" in tools.execute("read_thoughts", from_=3, to=1)

    def test_nan_and_empty_fields_render_as_empty_marker(self):
        details = pd.DataFrame([{"step_id": 1, "feedback": float("nan"), "summary": float("nan"),
                                 "thought": "", "action": "go north"}])
        steps = [make_step(1, action="go north"), make_step(2, is_done=True)]
        tools = RetrievalTools(make_extract(steps=steps, details=details), is_modular=True)
        assert "Step 1: (empty)" in tools.execute("read_summaries")

    def test_long_fields_are_truncated_with_marker(self):
        details = pd.DataFrame([{"step_id": 1, "feedback": "", "summary": "s" * 10000,
                                 "thought": "", "action": "go north"}])
        steps = [make_step(1, action="go north"), make_step(2, is_done=True)]
        tools = RetrievalTools(make_extract(steps=steps, details=details), is_modular=True)
        assert "[... truncated 6000 chars ...]" in tools.execute("read_summaries")

    def test_accounting_records_calls_and_total_chars(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        first = tools.execute("read_summaries")
        second = tools.execute("read_plan")
        assert tools.total_chars == len(first) + len(second)
        assert [call["tool"] for call in tools.calls] == ["read_summaries", "read_plan"]

    def test_accounting_tallies_channel_content_chars(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        tools.execute("read_summaries", from_=1, to=1)
        assert tools.channel_chars["summary"] == len("Started in kitchen")

    def test_read_steps_splits_accounting_across_channels(self):
        tools = RetrievalTools(make_three_step_extract(), is_modular=True)
        tools.execute("read_steps", from_=2, to=2)
        assert tools.channel_chars["observation"] == len("You entered a closet.")
        assert tools.channel_chars["thought"] == len("Now take the coin.")
        assert tools.channel_chars["action"] == len("take coin")

class FakeModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.model_version = "fake-1"
        self.step_cached_tokens = 0
        self.step_input_tokens = 10
        self.step_reasoning_tokens = 0
        self.step_output_tokens = 5
        self.step_total_tokens = 15

    def reset_step(self):
        pass

    def get_response(self, messages):
        return self.responses.pop(0)

def make_session(responses, **kwargs):
    tools = RetrievalTools(make_three_step_extract(), is_modular=True)
    return AgenticSession(FakeModel(responses), tools, ActionParser(), "INTRO", **kwargs)

READS = '{"reads": [{"tool": "read_summaries"}]}'
DIAGNOSE = json.dumps({"diagnose": DIAGNOSIS})

class TestAgenticSession:

    def test_read_then_diagnose_returns_record(self):
        result = make_session([READS, DIAGNOSE]).run()
        assert result["outcome"] == "diagnosed"
        assert result["record"]["primary_cause"] == "direction-misread"
        assert result["read_turns"] == 1
        assert result["n_turns"] == 2

    def test_tool_results_are_appended_as_user_message(self):
        result = make_session([READS, DIAGNOSE]).run()
        assert result["messages"][0] == {"role": "user", "content": "INTRO"}
        assert result["messages"][2]["role"] == "user"
        assert "Started in kitchen" in result["messages"][2]["content"]

    def test_malformed_turn_gets_reminder_then_recovers(self):
        result = make_session(["no json here", READS, DIAGNOSE]).run()
        assert result["outcome"] == "diagnosed"
        assert any(message["content"] == FORMAT_REMINDER_AGENTIC for message in result["messages"])

    def test_two_consecutive_malformed_turns_abort(self):
        result = make_session(["no json", "still no json"]).run()
        assert result["outcome"] == "malformed"
        assert result["record"] is None

    def test_valid_turn_resets_the_malformed_strike_counter(self):
        result = make_session(["no json", READS, "no json again", DIAGNOSE]).run()
        assert result["outcome"] == "diagnosed"

    def test_too_many_reads_in_one_turn_counts_as_protocol_error(self):
        seven = json.dumps({"reads": [{"tool": "read_plan"}] * 7})
        result = make_session([seven, READS, DIAGNOSE]).run()
        assert result["outcome"] == "diagnosed"
        assert result["read_turns"] == 1
        assert any("6" in message["content"] for message in result["messages"] if message["role"] == "user")

    def test_reads_after_budget_exhaustion_get_budget_message(self):
        result = make_session([READS, READS, DIAGNOSE], max_read_turns=1).run()
        assert result["outcome"] == "diagnosed"
        assert result["read_turns"] == 1
        assert any(message["content"] == BUDGET_MESSAGE for message in result["messages"])

    def test_persistent_reads_after_budget_exhaustion_abort(self):
        result = make_session([READS, READS, READS], max_read_turns=1).run()
        assert result["outcome"] == "budget-exhausted"
        assert result["record"] is None

    def test_turn_tokens_recorded_per_model_call(self):
        result = make_session([READS, DIAGNOSE]).run()
        assert len(result["turn_tokens"]) == 2
        assert result["turn_tokens"][0] == {"cached": 0, "input": 10, "reasoning": 0, "output": 5}

class TestBuildIntro:

    def test_modular_intro_lists_all_modular_tools_and_episode_facts(self):
        intro = build_intro("Find the coin.", 75, is_modular=True)
        assert "=== TASK ===\nFind the coin." in intro
        assert "The episode ran 75 steps and ended in failure." in intro
        assert "Steps are numbered 1-75." in intro
        for tool in ("read_summaries", "read_plan_updates", "read_memory_updates",
                     "read_plan()", "read_memories()", "read_steps"):
            assert tool in intro
        assert "`summarizer`, `memorizer`, `planner`, `reasoner`, or `actor`" in intro

    def test_react_intro_excludes_artifact_tools_and_forces_null_module(self):
        intro = build_intro("Find the coin.", 30, is_modular=False)
        assert "read_summaries" not in intro
        assert "read_plan" not in intro
        assert "read_memor" not in intro
        assert "always null — this agent has no module decomposition" in intro

    def test_both_intros_carry_the_frozen_taxonomy(self):
        for is_modular in (True, False):
            intro = build_intro("t", 5, is_modular)
            assert "position-miscount-skip" in intro
            assert "other — Escape class" in intro
            assert '{ "diagnose": {' in intro

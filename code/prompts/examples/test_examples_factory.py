import pytest
from params.parameters import Parameters
from memory.memory_manager import MemoryManager
from prompts.examples.examples_factory import ExamplesFactory


def all_on_params():
    return Parameters(
        use_summarizer=True,
        use_planner=True,
        use_memorizer=True,
        use_reasoner=True,
        use_actor=True,
        use_modular_single=True)


def get_example(examples: str, step: int) -> str:
    return examples.split(f"## Example {step}\n")[1].split(f"## Example {step + 1}\n")[0]


def parse_memories(step: int) -> dict:
    text = ExamplesFactory.get_part(step, "input-memories")
    if text.startswith("Memories: N/A"):
        return {}
    memories = {}
    for line in text.splitlines()[1:]:
        if line.strip():
            key, value = line.strip().split(":", 1)
            memories[key.strip()] = value.strip()
    return memories


def parse_plan(step: int) -> str:
    text = ExamplesFactory.get_part(step, "input-plan")
    if text.startswith("Plan: N/A"):
        return ""
    lines = [line[2:] for line in text.splitlines()[1:] if line.strip()]
    return "\n".join(lines)


class TestExamplesFactory:

    def test_create_for_all_subagents_disabled_input(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_summarizer=False,
            use_planner=False,
            use_memorizer=False,
            use_reasoner=False)
        examples = factory.create(params, "actor")

        assert "Task: " in examples # Always included
        assert "History:" not in examples
        assert "  Step 1: " not in examples
        assert "Memories:" not in examples
        assert "  living room: "
        assert "Plan:" not in examples
        assert "  - [x]" not in examples
        assert "  - [ ]" not in examples

    def test_create_for_all_subagents_enabled_input(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_summarizer=True,
            use_planner=True,
            use_memorizer=True,
            use_reasoner=True)
        examples = factory.create(params, "actor")

        # Pre-env fields
        assert "Task: " in examples # Always included
        assert "History:" in examples
        assert "  Step 1:" in examples
        assert "Memories:" in examples
        assert "  living room: " in examples
        assert "Plan:" in examples
        assert "  - [x]" in examples
        assert "  - [ ]" in examples

    @pytest.mark.parametrize("subagent, output", [
        ("summarizer", "start → location = living room"),
        ("memorizer", "living room: rooms = {north = ?}"),
        ("planner", "- [x] Take the gold key"),
        ("reasoner", "To dice the carrot, I need to go to the kitchen."),
        ("actor", "take gold key from shelf"),
    ])
    def test_create_for_subagent_output(self, subagent, output):
        factory = ExamplesFactory()
        params = Parameters()
        examples = factory.create(params, subagent)

        assert output in examples


class TestExamplesFactoryModularSingle:

    def test_output_sections_in_execution_order(self):
        examples = ExamplesFactory().create(all_on_params(), "modular-single")
        for step in range(1, 9):
            output = get_example(examples, step).split("### Output\n")[1]
            headers = [line for line in output.splitlines() if line.startswith("## ")]
            assert headers == ["## Summary", "## Memory", "## Plan", "## Thought", "## Action"]

    def test_output_section_contents(self):
        examples = ExamplesFactory().create(all_on_params(), "modular-single")
        example = get_example(examples, 1)
        assert "## Summary\nstart → location = living room" in example
        assert "## Plan\n- [ ] Find the kitchen" in example
        assert "## Action\ntake gold key from shelf" in example

    def test_no_change_plan_appears_in_examples(self):
        examples = ExamplesFactory().create(all_on_params(), "modular-single")
        assert "## Plan\nNO_CHANGE" in get_example(examples, 7)

    def test_input_uses_pre_update_memories_and_plan(self):
        examples = ExamplesFactory().create(all_on_params(), "modular-single")
        input_block = get_example(examples, 2).split("### Output")[0]
        assert "gold key: location = {room = living room, on = shelf}" in input_block
        assert "gold key: location = inventory" not in input_block

    def test_input_includes_previous_step_env_and_agent(self):
        examples = ExamplesFactory().create(all_on_params(), "modular-single")
        input_block = get_example(examples, 2).split("### Output")[0]
        assert "Step: 1 of 10" in input_block
        assert "Environment:" in input_block
        assert "  Thought: To dice the carrot" in input_block
        assert "  Action: take gold key from shelf" in input_block

    def test_toggles_gate_examples(self):
        examples = ExamplesFactory().create(Parameters(), "modular-single")
        assert "History:" not in examples
        assert "Memories:" not in examples
        assert "## Summary" not in examples
        assert "## Memory" not in examples
        assert "## Plan" not in examples
        assert "## Thought" not in examples
        assert "## Action" in examples

    def test_memory_updates_are_consistent_across_steps(self):
        manager = MemoryManager()
        for step in range(1, 10):
            memories = parse_memories(step)
            updates = ExamplesFactory.get_part(step, "output-memory").strip()
            assert manager.execute(memories, updates) == parse_memories(step + 1)

    def test_plan_updates_are_consistent_across_steps(self):
        for step in range(1, 10):
            output_plan = ExamplesFactory.get_part(step, "output-plan").strip()
            expected = parse_plan(step) if output_plan == "NO_CHANGE" else output_plan
            assert parse_plan(step + 1) == expected

    def test_summaries_are_consistent_with_history(self):
        # step-10 has no input-history part (only memories/plan), so stop at step 8 → 9
        for step in range(1, 9):
            summary = ExamplesFactory.get_part(step, "output-summary").strip()
            history = ExamplesFactory.get_part(step + 1, "input-history")
            assert f"Step {step}: {summary}" in history


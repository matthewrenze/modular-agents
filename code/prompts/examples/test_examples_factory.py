import sys
import pytest
from params.parameters import Parameters
from prompts.examples.examples_factory import ExamplesFactory

def create_full_params(k: int) -> Parameters:
    return Parameters(
        k=k,
        use_summarizer=True,
        use_planner=True,
        use_memorizer=True,
        use_reasoner=True)

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

    # Each example mirrors min(k, s - 1) previous steps; over the 9 example
    # steps that totals 8 at k=1, 30 at k=5, and 36 from k=8 up.
    @pytest.mark.parametrize("k, previous_steps", [
        (1, 8), (5, 30), (10, 36), (sys.maxsize, 36)])
    @pytest.mark.parametrize("subagent", [
        "summarizer", "memorizer", "planner", "reasoner", "actor"])
    def test_create_mirrors_k_previous_steps(self, subagent, k, previous_steps):
        factory = ExamplesFactory()
        examples = factory.create(create_full_params(k), subagent)

        # The actor also renders an "Agent:" block for the current step
        expected = previous_steps + 9 if subagent == "actor" else previous_steps
        assert examples.count("Agent:\n") == expected

    def test_create_k10_and_kn_examples_are_identical(self):
        factory = ExamplesFactory()
        examples_k10 = factory.create(create_full_params(10), "actor")
        examples_kn = factory.create(create_full_params(sys.maxsize), "actor")
        assert examples_k10 == examples_kn

    def test_create_previous_steps_stay_ordered(self):
        factory = ExamplesFactory()
        examples = factory.create(create_full_params(5), "planner")
        last_example = examples[examples.index("## Example 9"):]
        positions = [last_example.index(f"Step: {step} of 10") for step in range(4, 9)]
        assert positions == sorted(positions)

    @pytest.mark.parametrize("k", [5, 10, sys.maxsize])
    def test_create_react_examples_unchanged_at_every_k(self, k):
        factory = ExamplesFactory()
        examples_k1 = factory.create(Parameters(k=1), "react-k")
        examples_k = factory.create(Parameters(k=k), "react-k")
        assert examples_k == examples_k1


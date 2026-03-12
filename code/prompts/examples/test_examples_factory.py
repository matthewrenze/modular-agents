import pytest
from params.parameters import Parameters
from prompts.examples.examples_factory import ExamplesFactory

class TestExamplesFactory:

    def test_create_for_all_subagents_disabled_input(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=False,
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
            use_tasker=True,
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


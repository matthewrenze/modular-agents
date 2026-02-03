import pytest
from common.parameters import Parameters
from prompts.examples.examples_factory import ExamplesFactory

class TestExamplesFactory:

    def test_create_with_all_subagents_disabled(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=False,
            use_summarizer=False,
            use_memorizer=False,
            use_reasoner=False)
        examples = factory.create(params)

        assert "Task: " in examples # Always included
        assert "History:" not in examples
        assert "  Step 1: " not in examples
        assert "Memories:" not in examples
        assert "  1: "
        assert "  Summary: " not in examples
        assert "  Memory: " not in examples
        assert "  Thought: " not in examples
        assert "  Action: " in examples # Always included

    def test_create_with_all_subagents_enabled(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=True,
            use_summarizer=True,
            use_memorizer=True,
            use_reasoner=True)
        examples = factory.create(params)
        assert "Task: " in examples # Always included
        assert "History:" in examples
        assert "  Step 1:" in examples
        assert "Memories:" in examples
        assert "  1: " in examples
        assert "  Summary: " in examples
        assert "  Memory: " in examples
        assert "  Thought: " in examples
        assert "  Action: " in examples # Always included

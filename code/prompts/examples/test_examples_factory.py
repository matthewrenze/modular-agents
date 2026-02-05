import pytest
from common.parameters import Parameters
from prompts.examples.examples_factory import ExamplesFactory

class TestExamplesFactory:

    def test_create_with_all_subagents_disabled(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=False,
            use_summarizer=False,
            use_planner=False,
            use_memorizer=False,
            use_reasoner=False)
        examples = factory.create(params)

        # Pre-env fields
        assert "Task: " in examples # Always included
        assert "History:" not in examples
        assert "  Step 1: " not in examples
        assert "Plan:" not in examples
        assert "  1 [X]" not in examples
        assert "  2 [ ]" not in examples
        assert "Memories:" not in examples
        assert "  1: "

        # Agent fields
        assert "  Summary: " not in examples
        assert "  Plan: " not in examples
        assert "    add: " not in examples
        assert "    insert: " not in examples
        assert "    update: " not in examples
        assert "    mark: " not in examples
        assert "    delete: " not in examples
        assert "  Memory: " not in examples
        assert "    create: " not in examples
        assert "    delete: " not in examples
        assert "  Thought: " not in examples
        assert "  Action: " in examples # Always included

    def test_create_with_all_subagents_enabled(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=True,
            use_summarizer=True,
            use_planner=True,
            use_memorizer=True,
            use_reasoner=True)
        examples = factory.create(params)

        # Pre-env fields
        assert "Task: " in examples # Always included
        assert "History:" in examples
        assert "  Step 1:" in examples
        assert "Plan:" in examples
        assert "  1 [X]" in examples
        assert "  2 [ ]" in examples
        assert "Memories:" in examples
        assert "  1: " in examples

        # Agent fields
        assert "  Summary: " in examples
        assert "  Plan: " in examples
        assert "    add: " in examples
        assert "    insert: " in examples
        assert "    update: " in examples
        assert "    mark: " in examples
        assert "    delete: " in examples
        assert "  Memory: " in examples
        assert "    create: " in examples
        assert "    delete: " in examples
        assert "  Thought: " in examples
        assert "  Action: " in examples # Always included

import pytest
from common.parameters import Parameters
from prompts.examples.examples_factory import ExamplesFactory

class TestExamplesFactory:

    def test_create_with_all_subagents_disabled(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=False,
            use_reasoner=False)
        examples = factory.create(params)

        assert "Task: " in examples # Always included
        assert "Thought: " not in examples
        assert "Action: " in examples # Always included

    def test_create_with_all_subagents_enabled(self):
        factory = ExamplesFactory()
        params = Parameters(
            use_tasker=True,
            use_reasoner=True)
        examples = factory.create(params)
        assert "Task: " in examples # Always included
        assert "Thought: " in examples
        assert "Action: " in examples # Always included

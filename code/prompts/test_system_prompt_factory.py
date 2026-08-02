import sys
from params.parameters import Parameters
from prompts.system_prompt_factory import SystemPromptFactory

system_prompt_template = """
# System
{system}

# Actions
{actions}

# Process
{process}

# Constraints
We have {max_steps} steps to complete each task.

# Examples
{examples}
"""

class TestSystemPromptFactory:
    def test_create(self):
        factory = SystemPromptFactory()
        params = Parameters(
            max_steps=99)
        subagent = "actor"
        system_prompt = factory.create(params, subagent, system_prompt_template)
        assert "# System" in system_prompt
        assert "{system}" not in system_prompt
        assert "# Process" in system_prompt
        assert "{process}" not in system_prompt
        assert "# Actions" in system_prompt
        assert "{actions}" not in system_prompt
        assert "{max_steps}" not in system_prompt
        assert "We have 99 steps to complete each task." in system_prompt
        assert "# Examples" in system_prompt
        assert "{examples}" not in system_prompt

    def test_create_context_at_k1(self):
        factory = SystemPromptFactory()
        assert factory.create_context(Parameters(k=1), "actor") == "the previous step and the current step"
        assert factory.create_context(Parameters(k=1), "planner") == "the current step"

    def test_create_context_at_finite_k(self):
        factory = SystemPromptFactory()
        assert factory.create_context(Parameters(k=5), "actor") == "the previous 5 steps and the current step"
        assert factory.create_context(Parameters(k=5), "planner") == "the previous 5 steps and the current step"

    def test_create_context_at_kn(self):
        factory = SystemPromptFactory()
        assert factory.create_context(Parameters(k=sys.maxsize), "actor") == "all previous steps and the current step"
        assert factory.create_context(Parameters(k=sys.maxsize), "planner") == "all previous steps and the current step"
import pytest
from common.parameters import Parameters
from prompts.system.system_factory import SystemFactory

class TestSystemFactory:
    def test_create_for_all_subagents_disabled(self):
        factory = SystemFactory()
        params = Parameters(
            use_tasker=False,
            use_reasoner=False,
            use_summarizer=False)
        system_prompt = factory.create(params, "actor")
        assert not "  - Tasker - " in system_prompt
        assert not "  - Reasoner - " in system_prompt
        assert "  - Actor (you) - " in system_prompt
        assert not "  - Summarizer - " in system_prompt

    def test_create_for_all_subagents_enabled(self):
        factory = SystemFactory()
        params = Parameters(
            use_tasker=True,
            use_summarizer=True,
            use_reasoner=True)
        system_prompt = factory.create(params, "actor")
        assert "  - Tasker - " in system_prompt
        assert "  - Reasoner - " in system_prompt
        assert "  - Actor (you) - " in system_prompt
        assert "  - Summarizer - " in system_prompt

    @pytest.mark.parametrize(
        "subagent_name, subagent_tag",
        [("tasker", "  - Tasker (you) - "),
         ("reasoner", "  - Reasoner (you) - "),
         ("actor", "  - Actor (you) - "),
         ("summarizer", "  - Summarizer (you) - ")],
    )
    def test_create_for_subagent_you_tag(self, subagent_name, subagent_tag):
        factory = SystemFactory()
        params = Parameters(
            use_tasker=True,
            use_summarizer=True,
            use_reasoner=True)
        system_prompt = factory.create(params, subagent_name)
        assert subagent_tag in system_prompt

import pytest
from common.parameters import Parameters
from prompts.process.process_factory import ProcessFactory

class TestProcessFactory:

    def test_create_with_all_subagents_enabled(self):
        factory = ProcessFactory()
        params = Parameters(
            use_tasker=True,
            use_reasoner=True,
            use_summarizer=True)
        process_prompt = factory.create(params, "actor")
        assert " - Task (Tasker) - " in process_prompt
        assert " - Thought (Reasoner) - " in process_prompt
        assert " - Action (you) - " in process_prompt
        assert " - Summary (Summarizer) - " in process_prompt

    def test_create_with_all_subagents_disabled(self):
        factory = ProcessFactory()
        params = Parameters(
            use_tasker=False,
            use_reasoner=False,
            use_summarizer=False)
        process_prompt = factory.create(params, "actor")
        assert " - Task (Tasker) - " not in process_prompt
        assert " - Thought (Reasoner) - " not in process_prompt
        assert " - Action (you) - " in process_prompt
        assert " - Summary (Summarizer) - " not in process_prompt

    @pytest.mark.parametrize(
        "subagent_name, subagent_tag",
        [("tasker", "  - Task (you) - "),
         ("reasoner", "  - Thought (you) - "),
         ("actor", "  - Action (you) - "),
         ("summarizer", "  - Summary (you) - ")],
    )
    def test_create_for_subagent_you_tag(self, subagent_name, subagent_tag):
        factory = ProcessFactory()
        params = Parameters(
            use_tasker=True,
            use_reasoner=True,
            use_summarizer=True)
        system_prompt = factory.create(params, subagent_name)
        assert subagent_tag in system_prompt
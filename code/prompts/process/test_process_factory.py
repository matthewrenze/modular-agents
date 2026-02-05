import pytest
from common.parameters import Parameters
from prompts.process.process_factory import ProcessFactory

class TestProcessFactory:

    def test_create_with_all_subagents_enabled(self):
        factory = ProcessFactory()
        params = Parameters(
            use_tasker=True,
            use_summarizer=True,
            use_planner=True,
            use_memorizer=True,
            use_reasoner=True)
        process_prompt = factory.create(params, "actor")
        assert " - Task" in process_prompt
        assert " - History" in process_prompt
        assert " - Summary" in process_prompt
        assert " - Plan" in process_prompt
        assert " - Memories" in process_prompt
        assert " - Memory" in process_prompt
        assert " - Thought" in process_prompt
        assert " - Action (you) - " in process_prompt

    def test_create_with_all_subagents_disabled(self):
        factory = ProcessFactory()
        params = Parameters(
            use_tasker=False,
            use_summarizer=False,
            use_planner=False,
            use_memorizer=False,
            use_reasoner=False)
        process_prompt = factory.create(params, "actor")
        assert " - Task" not in process_prompt
        assert " - Summary" not in process_prompt
        assert " - History" not in process_prompt
        assert " - Plan" not in process_prompt
        assert " - Memories" not in process_prompt
        assert " - Memory" not in process_prompt
        assert " - Thought" not in process_prompt
        assert " - Action (you) - " in process_prompt

    @pytest.mark.parametrize(
        "subagent_name, subagent_tag",
        [("tasker", "  - Task (you) - "),
         ("summarizer", "  - Summary (you) - "),
         ("planner", "  - Plan (you) - "),
         ("memorizer", "  - Memory (you) - "),
         ("reasoner", "  - Thought (you) - "),
         ("actor", "  - Action (you) - ")],
    )
    def test_create_for_subagent_you_tag(self, subagent_name, subagent_tag):
        factory = ProcessFactory()
        params = Parameters(
            use_tasker=True,
            use_summarizer=True,
            use_planner=True,
            use_memorizer=True,
            use_reasoner=True)
        system_prompt = factory.create(params, subagent_name)
        assert subagent_tag in system_prompt
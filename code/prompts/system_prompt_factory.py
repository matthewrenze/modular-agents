from common.parameters import Parameters
from prompts.system.system_factory import SystemFactory
from prompts.process.process_factory import ProcessFactory
from prompts.actions.actions_factory import ActionsFactory
from prompts.examples.examples_factory import ExamplesFactory

class SystemPromptFactory:
    def create(self, params: Parameters, subagent: str, system_prompt: str) -> str:

        # Add system section
        system_factory = SystemFactory()
        system_content = system_factory.create(params, subagent)
        system_prompt = system_prompt.replace("{system}", system_content)

        # Add process section
        process_factory = ProcessFactory()
        process_content = process_factory.create(params, subagent)
        system_prompt = system_prompt.replace("{process}", process_content)

        # Add actions section
        actions_factory = ActionsFactory()
        actions_content = actions_factory.create()
        system_prompt = system_prompt.replace("{actions}", actions_content)

        # Add examples section
        examples_factory = ExamplesFactory()
        examples_content = examples_factory.create(params)
        system_prompt = system_prompt.replace("{examples}", examples_content)

        # Replace max steps
        system_prompt = system_prompt.replace("{max_steps}", str(params.max_steps))

        return system_prompt
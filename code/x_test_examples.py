from params.parameters import Parameters
from prompts.examples.examples_factory import ExamplesFactory

# subagent = "react-kn"
# subagent = "summarizer"
# subagent = "memorizer"
subagent = "planner"
# subagent = "reasoner"
# subagent = "actor"

params = Parameters(
    use_summarizer=True,
    use_planner=True,
    use_memorizer=True,
    use_reasoner=True)

factory = ExamplesFactory()
content = factory.create(params, subagent)

print(content)
from renderers.step.step_renderer import StepRenderer
from states.step_state import StepState
from states.task_state import TaskState
from states.env_state import EnvState
from states.agent_state import AgentState

class TestStepRenderer:
    def test_render_step(self):
        step_state = StepState(
            step_id=1,
            env_state=EnvState(),
            agent_state=AgentState())
        task_state = TaskState(max_steps=2)
        expected = "Step: 1 of 2\n"

        renderer = StepRenderer()
        actual = renderer.render(step_state, task_state)

        assert actual == expected
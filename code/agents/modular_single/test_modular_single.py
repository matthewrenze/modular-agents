from params.parameters import Parameters
from models.model import Model
from renderers.renderer_factory import RendererFactory
from agents.modular_single.modular_single import ModularSingle
from prompts.examples.examples_factory import ExamplesFactory
from states.global_state import GlobalState
from states.task_state import TaskState
from states.step_state import StepState
from states.env_state import EnvState
from states.agent_state import AgentState


RESPONSE = """## Summary
go north → location = kitchen
## Memory
kitchen: rooms = {south = living room}
living room: rooms = {north = kitchen}
## Plan
- [x] Find the kitchen
- [ ] Dice the orange carrot
## Thought
I am in the kitchen now, so I should look for the carrot.
## Action
take orange carrot from counter"""


class MockModel(Model):
    def __init__(self, response=RESPONSE):
        super().__init__("mock-model")
        self.response = response

    def get_response(self, messages):
        return self.response


def create_agent(response=RESPONSE, params=None):
    params = params or Parameters(
        use_summarizer=True,
        use_planner=True,
        use_memorizer=True,
        use_reasoner=True,
        use_actor=True,
        use_modular_single=True)
    renderer = RendererFactory.create()
    return ModularSingle(MockModel(response), renderer, "SYSTEM PROMPT", params)


def create_state(steps=1):
    state = GlobalState()
    state.task_state = TaskState(task="Dice the orange carrot.", step_id=steps, max_steps=20, max_items=5, max_score=2)
    state.memories = {"gold key": "location = inventory"}
    state.plan = "- [ ] Find the kitchen"
    for step_id in range(1, steps + 1):
        step_state = StepState(
            step_id=step_id,
            env_state=EnvState(location=f"location-{step_id}", description=f"description-{step_id}", feedback=f"feedback-{step_id}"),
            agent_state=AgentState(summary=f"summary-{step_id}", thought=f"thought-{step_id}", action=f"action-{step_id}"))
        state.step_history.append(step_state)
    return state


class TestModularSingleParser:

    def test_execute_parses_five_sections(self):
        agent = create_agent()
        summary, memory, plan, thought, action = agent.execute(create_state())
        assert summary == "go north → location = kitchen"
        assert memory == "kitchen: rooms = {south = living room}\nliving room: rooms = {north = kitchen}"
        assert plan == "- [x] Find the kitchen\n- [ ] Dice the orange carrot"
        assert thought == "I am in the kitchen now, so I should look for the carrot."
        assert action == "take orange carrot from counter"

    def test_missing_section_yields_empty_string(self):
        response = "## Summary\ngo north → location = kitchen\n## Plan\nNO_CHANGE\n## Thought\nA thought.\n## Action\ngo north"
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert summary == "go north → location = kitchen"
        assert memory == ""
        assert plan == "NO_CHANGE"
        assert thought == "A thought."
        assert action == "go north"

    def test_malformed_response_yields_all_empty(self):
        response = "I could not produce the requested sections."
        assert create_agent(response).execute(create_state()) == ("", "", "", "", "")

    def test_empty_sections_yield_empty_strings(self):
        response = "## Summary\n## Memory\n## Plan\n## Thought\n## Action"
        assert create_agent(response).execute(create_state()) == ("", "", "", "", "")

    def test_generic_header_lines_stay_inside_sections(self):
        response = RESPONSE.replace("I am in the kitchen now,", "## Notes\nI am in the kitchen now,")
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert "## Notes" in thought
        assert action == "take orange carrot from counter"

    def test_similar_header_lines_are_not_anchors(self):
        response = "## Summary\ngo north → location = kitchen\n## Actions\nnot an anchor\n## Action\ngo north"
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert summary == "go north → location = kitchen\n## Actions\nnot an anchor"
        assert action == "go north"

    def test_header_with_trailing_text_is_not_an_anchor(self):
        response = "## Summary\ngo north → location = kitchen\n## Action items\nnot an anchor\n## Action\ngo north"
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert "## Action items" in summary
        assert action == "go north"

    def test_duplicate_section_first_occurrence_wins(self):
        response = "## Summary\nfirst summary\n## Summary\nsecond summary\n## Action\ngo north"
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert summary == "first summary"
        assert action == "go north"

    def test_out_of_order_sections_still_parse(self):
        response = "## Action\ngo north\n## Summary\ngo north → location = kitchen"
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert summary == "go north → location = kitchen"
        assert action == "go north"

    def test_text_before_first_header_is_ignored(self):
        response = "Here is my response:\n" + RESPONSE
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert summary == "go north → location = kitchen"

    def test_blank_lines_between_sections_are_tolerated(self):
        response = RESPONSE.replace("\n## ", "\n\n## ")
        summary, memory, plan, thought, action = create_agent(response).execute(create_state())
        assert summary == "go north → location = kitchen"
        assert action == "take orange carrot from counter"


class TestModularSingleInput:

    def test_messages_structure(self):
        agent = create_agent()
        agent.execute(create_state())
        assert len(agent.messages) == 3
        assert agent.messages[0] == {"role": "system", "content": "SYSTEM PROMPT"}
        assert agent.messages[1]["role"] == "user"
        assert agent.messages[2] == {"role": "assistant", "content": RESPONSE}

    def test_first_step_input_blocks_in_order(self):
        agent = create_agent()
        agent.execute(create_state(steps=1))
        user_content = agent.messages[1]["content"]
        blocks = ["Task: Dice the orange carrot.", "History: N/A", "Memories:", "Plan:", "Step: 1 of 20", "Environment:"]
        indexes = [user_content.index(block) for block in blocks]
        assert indexes == sorted(indexes)
        assert "Agent:" not in user_content

    def test_later_step_input_blocks_in_order(self):
        agent = create_agent()
        agent.execute(create_state(steps=2))
        user_content = agent.messages[1]["content"]
        blocks = [
            "Task: Dice the orange carrot.",
            "History:",
            "  Step 1: summary-1",
            "Memories:",
            "  gold key: location = inventory",
            "Plan:",
            "  - [ ] Find the kitchen",
            "Step: 1 of 20",
            "location-1",
            "Agent:",
            "  Thought: thought-1",
            "  Action: action-1",
            "Step: 2 of 20",
            "location-2"]
        indexes = [user_content.index(block) for block in blocks]
        assert indexes == sorted(indexes)

    def test_previous_step_includes_environment(self):
        agent = create_agent()
        agent.execute(create_state(steps=2))
        user_content = agent.messages[1]["content"]
        assert "description-1" in user_content
        assert "description-2" in user_content

    def test_history_excludes_current_step(self):
        agent = create_agent()
        agent.execute(create_state(steps=2))
        user_content = agent.messages[1]["content"]
        assert "Step 1: summary-1" in user_content
        assert "Step 2: summary-2" not in user_content

    def test_toggles_gate_input_blocks(self):
        params = Parameters(
            use_summarizer=False,
            use_planner=False,
            use_memorizer=False,
            use_reasoner=True,
            use_actor=True,
            use_modular_single=True)
        agent = create_agent(params=params)
        agent.execute(create_state(steps=2))
        user_content = agent.messages[1]["content"]
        assert "History:" not in user_content
        assert "Memories:" not in user_content
        assert "Plan:" not in user_content

    def test_live_input_mirrors_example_input(self):
        # State reproducing the prompts/examples step-3 part files exactly
        state = GlobalState()
        state.task_state = TaskState(task="Dice the orange carrot in the kitchen.", step_id=3, max_steps=10, max_items=5, max_score=2)
        state.memories = {
            "living room": "rooms = {north = ?}, doors = {north = wooden door}",
            "wooden door": "location = living room, direction = north, state = {closed, locked}",
            "gold key": "location = inventory"}
        state.plan = "- [ ] Find the kitchen\n" \
            "  - [x] Take the gold key\n" \
            "  - [ ] Unlock the wooden door\n" \
            "  - [ ] Open the wooden door\n" \
            "  - [ ] Go north to the kitchen\n" \
            "- [ ] Dice the orange carrot"
        state.step_history = [
            StepState(
                step_id=1,
                env_state=EnvState(),
                agent_state=AgentState(summary="start → location = living room")),
            StepState(
                step_id=2,
                env_state=EnvState(
                    feedback="You take the gold key from the shelf.",
                    location="Living Room",
                    description="You are in a cozy living room. There is a locked wooden door to the north.",
                    inventory="You are carrying: a gold key.",
                    items=1),
                agent_state=AgentState(
                    summary="take gold key from shelf → inventory += gold key",
                    thought="Now that I have the gold key in my inventory, I can use it to unlock the wooden door to the north.",
                    action="unlock wooden door with gold key")),
            StepState(
                step_id=3,
                env_state=EnvState(
                    feedback="You unlock the wooden door with the gold key.",
                    location="Living Room",
                    description="You are in a cozy living room. There is an unlocked wooden door to the north.",
                    inventory="You are carrying: a gold key.",
                    items=1),
                agent_state=AgentState())]

        agent = create_agent()
        agent.execute(state)
        live_input = agent.messages[1]["content"]

        examples = ExamplesFactory().create(agent.params, "modular-single")
        example = examples.split("## Example 3\n")[1].split("## Example 4\n")[0]
        example_input = example.split("### Input\n")[1].split("\n### Output\n")[0]

        def content_lines(text):
            return [line.rstrip() for line in text.splitlines() if line.strip()]

        assert content_lines(live_input) == content_lines(example_input)

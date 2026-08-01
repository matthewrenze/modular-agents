import re
from agents.agent import Agent
from states.global_state import GlobalState

class ModularSingle(Agent):

    # Anchors only on the five exact section headers at line start
    section_pattern = r"^## (Summary|Memory|Plan|Thought|Action)[ \t]*$\n?"

    def execute(self, state: GlobalState) -> tuple[str, str, str, str, str]:

        # Clear the previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Add the task
        user_content = self.renderer.render_task(state.task_state)
        user_content += "\n"

        # Add the history
        if self.params.use_summarizer:
            previous_steps = state.step_history[:-1]
            user_content += self.renderer.render_history(previous_steps)
            user_content += "\n"

        # Add the memories
        if self.params.use_memorizer:
            user_content += self.renderer.render_memories(state.memories)
            user_content += "\n"

        # Add the plan
        if self.params.use_planner:
            user_content += self.renderer.render_plan(state.plan)
            user_content += "\n"

        # Add the previous step (env + agent)
        if len(state.step_history) >= 2:
            previous_step = state.step_history[-2]
            user_content += self.renderer.render_step(previous_step, state.task_state)
            user_content += self.renderer.render_env(previous_step.env_state, state.task_state)
            user_content += self.renderer.render_agent(previous_step.agent_state)
            user_content += "\n"

        # Add the current environment
        current_step = state.step_history[-1]
        user_content += self.renderer.render_step(current_step, state.task_state)
        user_content += self.renderer.render_env(current_step.env_state, state.task_state)
        user_content += "\n"

        # Add the user prompt
        user_message = {"role": "user", "content": user_content}
        self.messages.append(user_message)

        # Get the response from the model
        response = self.model.get_response(self.messages)
        response = response.replace("\n\n", "\n")
        response = response.strip()

        # Add the response to the messages
        response_message = {"role": "assistant", "content": response}
        self.messages.append(response_message)

        # Parse the five sections (a missing section yields "")
        sections = self.get_sections(response)
        summary = sections.get("Summary", "")
        memory = sections.get("Memory", "")
        plan = sections.get("Plan", "")
        thought = sections.get("Thought", "")
        action = sections.get("Action", "")

        return summary, memory, plan, thought, action

    @classmethod
    def get_sections(cls, response: str) -> dict[str, str]:
        parts = re.split(cls.section_pattern, response, flags=re.MULTILINE)
        sections = {}
        for index in range(1, len(parts) - 1, 2):
            sections.setdefault(parts[index], parts[index + 1].strip())
        return sections

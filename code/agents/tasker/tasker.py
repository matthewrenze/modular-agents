from agents.agent import Agent
from states.global_state import GlobalState

class Tasker(Agent):

    def execute(self, state: GlobalState) -> str:

        # Clear the previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Add the task
        user_content = self.renderer.render_task(state.task_state)
        user_content += "\n"

        # Add the first step
        step = state.step_history[0]
        user_content += self.renderer.render_step(step, state.task_state)
        user_content += self.renderer.render_env(step.env_state, state.task_state)
        user_content += self.renderer.render_agent(step.agent_state)

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

        return response
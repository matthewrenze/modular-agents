import re
from common.console import debug
from states.global_state import GlobalState
from agents.agent import Agent

class ReactAgent(Agent):

    def reset(self):
        self.model.reset()
        system_content = self.system_prompt.strip()
        system_message = {"role": "system", "content": system_content}
        self.messages = [system_message]

    def execute(self, state: GlobalState) -> tuple[str, str]:

        # Add the task to the first user prompt
        user_content = ""
        if state.task_state.step_id == 1:
            user_content += self.renderer.render_task(state.task_state)

        # Add the last step
        step_state = state.step_history[-1]
        user_content + self.renderer.render_step(step_state, state.task_state)
        user_content += self.renderer.render_env(step_state.env_state, state.task_state)
        user_content += "\n"

        # Append the user message
        user_message = {"role": "user", "content": user_content}
        self.messages.append(user_message)

        # Get the response from the model
        response = self.model.get_response(self.messages)
        response = response.replace("\n\n", "\n")
        response = response.strip()

        # Get the thought from the response
        thought_match = re.search(r"Thought: (.*?)(?=\nAction:)", response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""

        # Get the action from the response
        action_match = re.search(r"Action: (.*)", response, re.DOTALL)
        action = action_match.group(1).strip() if action_match else ""

        # Add the response to the messages
        response_message = {"role": "assistant", "content": response}
        self.messages.append(response_message)

        return thought, action


# # DEBUG:
# class TestModel:
#     def get_response(self, prompt):
#         return "Thought: This is a mock thought.\nAction: Finish[mock answer]"
# model = TestModel()
# agent = Agent(model)
# action = agent.act("Mock observation for testing.")
# print(agent.prompt)
# print(action)
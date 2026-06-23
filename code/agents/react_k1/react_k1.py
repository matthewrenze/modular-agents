import re
from states.global_state import GlobalState
from agents.agent import Agent

class ReactK1(Agent):

    def reset(self):
        self.model.reset()
        system_content = self.system_prompt.strip()
        system_message = {"role": "system", "content": system_content}
        self.messages = [system_message]

    def execute(self, state: GlobalState) -> tuple[str, str]:

        # Clear previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Add the task message
        task_user_content = self.renderer.render_task(state.task_state)
        task_message = {"role": "user", "content": task_user_content}
        self.messages.append(task_message)

        # Add the previous step user (env) message
        if len(state.step_history) > 1:
            previous_step = state.step_history[-2]
            previous_user_content = self.renderer.render_step(previous_step, state.task_state)
            previous_user_content += self.renderer.render_env(previous_step.env_state, state.task_state)
            previous_user_message = {"role": "user", "content": previous_user_content}
            self.messages.append(previous_user_message)

            # Add the previous step model (agent) message
            previous_agent_state = previous_step.agent_state
            previous_agent_content = f"Thought: {previous_agent_state.thought}\nAction: {previous_agent_state.action}"
            previous_agent_message = {"role": "assistant", "content": previous_agent_content}
            self.messages.append(previous_agent_message)

        # Add the current step's user (env) message
        current_step = state.step_history[-1]
        current_user_content = self.renderer.render_step(current_step, state.task_state)
        current_user_content += self.renderer.render_env(current_step.env_state, state.task_state)
        prompt_message = {"role": "user", "content": current_user_content}
        self.messages.append(prompt_message)

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
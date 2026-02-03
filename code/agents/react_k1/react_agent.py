import re
from common.console import debug
from states.global_state import GlobalState
from agents.agent import Agent

class ReactAgentK1(Agent):

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

        # Create the task prompt
        task_state = state.task_state
        task_user_content = ""
        task_user_content += f"Task: {task_state.task}\n"

        # Add the task message
        task_message = {"role": "user", "content": task_user_content}
        self.messages.append(task_message)

        # Create the previous step's env state
        if len(state.step_history) > 1:
            previous_state = state.step_history[-2]
            previous_env_state = previous_state.env_state
            previous_user_content = f"# Step: {previous_state.step_id} of {task_state.max_steps}\n"
            previous_user_content += f"Environment:\n" \
                + f"  Feedback: {previous_env_state.feedback}\n" \
                + f"  Location: {previous_env_state.location}\n" \
                + f"  Description: {previous_env_state.description}\n" \
                + f"  Inventory: {previous_env_state.inventory}\n" \
                + f"  Capacity: {previous_env_state.items} of {task_state.max_items} items\n" \
                + f"  Score: {previous_env_state.score} of {task_state.max_score}\n" \
                + f"  Done: {previous_env_state.is_done}\n" \
                + "\n"

            # Add the previous user message
            previous_user_message = {"role": "user", "content": previous_user_content}
            self.messages.append(previous_user_message)

            # Create the previous step's agent state
            previous_agent_state = previous_state.agent_state
            previous_agent_content = f"Agent:\n" \
                + f"  Thought: {previous_agent_state.thought}\n" \
                + f"  Action: {previous_agent_state.action}\n" \
                + "\n"

            # Add the previous agent message
            previous_agent_message = {"role": "assistant", "content": previous_agent_content}
            self.messages.append(previous_agent_message)

        # Create the current user prompt
        current_state = state.step_history[-1]
        env_state = current_state.env_state
        current_user_content = f"# Step: {current_state.step_id} of {task_state.max_steps}\n"
        current_user_content += f"Environment:\n" \
            + f"  Feedback: {current_state.env_state.feedback}\n" \
            + f"  Location: {current_state.env_state.location}\n" \
            + f"  Description: {current_state.env_state.description}\n" \
            + f"  Inventory: {current_state.env_state.inventory}\n" \
            + f"  Capacity: {env_state.items} of {task_state.max_items} items\n" \
            + f"  Score: {env_state.score} of {task_state.max_score}\n" \
            + f"  Done: {env_state.is_done}\n" \
            + "\n"

        # Add the current user message
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
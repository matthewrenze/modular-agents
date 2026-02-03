from agents.agent import Agent
from states.global_state import GlobalState

class Tasker(Agent):

    def execute(self, state: GlobalState) -> str:

        # Clear the previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Add the task to the user prompt
        task_state = state.task_state
        user_content = f"Task: {task_state.task}\n"

        # Get initial step from the history
        step = state.step_history[0]

        # Get the initial state
        env_state = step.env_state
        user_content += f"# Step: {step.step_id} of {task_state.max_steps}\n"

        # Append the environment state
        user_content += f"Environment:\n" \
            + f"  Location: {step.env_state.location}\n" \
            + f"  Description: {step.env_state.description}\n" \
            + f"  Inventory: {step.env_state.inventory}\n" \
            + f"  Capacity: {env_state.items} of {task_state.max_items} items\n" \
            + f"  Score: {env_state.score} of {task_state.max_score}\n" \
            + f"  Done: {env_state.is_done}\n" \
            + "\n"

        user_message = {"role": "user", "content": user_content}

        # Add the user prompt
        self.messages.append(user_message)

        # Get the response from the model
        response = self.model.get_response(self.messages)
        response = response.replace("\n\n", "\n")
        response = response.strip()

        # Add the response to the messages
        response_message = {"role": "assistant", "content": response}
        self.messages.append(response_message)

        return response
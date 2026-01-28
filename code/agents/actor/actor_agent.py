from agents.agent import Agent
from states.global_state import GlobalState

class ActorAgent(Agent):

    def execute(self, state: GlobalState) -> str:

        # Clear the previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Add the task to the user prompt
        task_state = state.task_state
        user_content = f"Task: {task_state.task}\n"

        # Get the previous five steps (plus current step) from the history
        previous_steps = state.step_history[-6:]

        for index, step in enumerate(previous_steps):
            env_state = step.env_state
            agent_state = step.agent_state
            user_content += f"# Step: {step.step_id} of {task_state.max_steps}\n"

            # Append the environment state
            user_content += f"Environment:\n" \
                + f"  Feedback: {step.env_state.feedback}\n" \
                + f"  Location: {step.env_state.location}\n" \
                + f"  Description: {step.env_state.description}\n" \
                + f"  Inventory: {step.env_state.inventory}\n" \
                + f"  Capacity: {env_state.items} of {task_state.max_items} items\n" \
                + f"  Score: {env_state.score} of {task_state.max_score}\n" \
                + f"  Done: {env_state.is_done}\n" \
                + "\n"

            # For the last step, only include the thought
            if index == len(previous_steps) - 1:
                user_content += f"Agent:\n" \
                    + f"  Thought: {agent_state.thought}\n" \

            else:
                user_content += f"Agent:\n" \
                    + f"  Thought: {agent_state.thought}\n" \
                    + f"  Action: {agent_state.action}\n" \
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
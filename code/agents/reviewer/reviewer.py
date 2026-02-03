import yaml
from agents.agent import Agent
from states.global_state import GlobalState
from reviews.review import Review

class Reviewer(Agent):

    def execute(self, state: GlobalState) -> str:
        raise NotImplementedError("Reviewer does not implement execute() method. Use review() instead.")

    def review(self, state: GlobalState, raw_task: str, solution: str) -> Review:

        # Clear the previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Add the pre-fixes to the user prompt
        task_state = state.task_state
        user_content = f"Original Task: {raw_task}\n" \
            + f"Revised Task: {task_state.task}\n" \
            + f"Solution: {solution}\n" \
            + f"Max Steps: {task_state.max_steps}\n" \
            + "\n"

        # Get the previous steps from the history
        previous_steps = state.step_history

        for index, step in enumerate(previous_steps):
            env_state = step.env_state
            agent_state = step.agent_state
            user_content += f"Step: {step.step_id} of {task_state.max_steps}\n"

            # Append the environment state
            user_content += f"Environment:\n" \
                + f"  Feedback: {env_state.feedback}\n" \
                + f"  Location: {env_state.location}\n" \
                + f"  Description: {env_state.description}\n" \
                + f"  Inventory: {env_state.inventory}\n" \
                + f"  Capacity: {env_state.items} of {task_state.max_items}\n" \
                + f"  Score: {env_state.score} of {task_state.max_score}\n" \
                + f"  Done: {env_state.is_done}\n"

            # For the last step, don't include the observation
            if index == len(previous_steps) - 1:
                continue

            # Append the agent state
            user_content += f"Agent State:\n" \
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

        # Parse the review
        review = Review()
        parsed = yaml.safe_load(response)
        review.steps = parsed.get("Steps", "")
        review.loops = parsed.get("Loops", "")
        review.summary = parsed.get("Summary", "")
        review.category = parsed.get("Category", "")
        review.advice = parsed.get("Advice", "")

        return review

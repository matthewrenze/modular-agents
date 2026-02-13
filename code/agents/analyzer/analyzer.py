import yaml
from agents.agent import Agent
from states.global_state import GlobalState

class Analyzer(Agent):

    def execute(self, state: GlobalState) -> str:
        raise NotImplementedError("Reviewer does not implement execute() method. Use review() instead.")

    def analyze(self, reviews: str) -> str:

        # Clear the previous messages
        self.messages = []

        # Add the system prompt
        system_message = {"role": "system", "content": self.system_prompt.strip()}
        self.messages.append(system_message)

        # Create the user content
        user_content = reviews.strip()

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

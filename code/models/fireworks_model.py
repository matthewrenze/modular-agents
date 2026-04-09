import os
import time
from fireworks import Fireworks
from logs.console import warn
from models.model import Model

class FireworksModel(Model):
    def __init__(self, model_name):
        super().__init__(model_name)

        api_key = os.environ.get("FIREWORKS_API_KEY")
        self.client = Fireworks(api_key=api_key)

    def get_response(self, messages):

        # Create the fireworks model name
        model_name = self.model_name.replace(".", "p")
        model_name = f"accounts/fireworks/models/{model_name}"

        # Hack to make GLM-5-fast work
        if model_name.endswith("glm-5-fast"):
            model_name = f"accounts/fireworks/routers/glm-5-fast"

        # Create the parameters
        params = {
            "model": model_name,
            "messages": messages,
            "top_p": 1.0,
            "temperature": 0.0,
        }

        # Set retry variables
        retries = [10, 20, 30, 60, 180, 300, 600, 1200, 1200]  # wait before each retry
        attempts = 0

        while True:
            try:
                # Get the response
                response = self.client.chat.completions.create(**params)

                # Get the content
                content = response.choices[0].message.content

                # Handle empty response
                if content is None:
                    raise ValueError("Received empty response from LLM API.")

                # Get tokens
                cached_tokens = getattr(response.usage.prompt_tokens_details, "cached_tokens", 0)
                prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
                completion_tokens = getattr(response.usage, "completion_tokens", 0)
                total_tokens = getattr(response.usage, "total_tokens", 0)

                # Update tokens
                self.update_tokens(
                    cached_tokens=cached_tokens,
                    input_tokens=prompt_tokens - cached_tokens,
                    reasoning_tokens=0,
                    output_tokens=completion_tokens,
                    total_tokens=total_tokens)

                return content
            except Exception as e:

                if attempts >= len(retries):
                    raise

                delay = retries[attempts]
                warn(f"Retrying LLM API call in {delay} seconds due to error: {e}")
                time.sleep(delay)
                self.wait_time += delay
                attempts += 1

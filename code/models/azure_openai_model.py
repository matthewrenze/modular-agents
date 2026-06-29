import os
import time
from openai import AzureOpenAI
from logs.console import warn
from models.model import Model

class AzureOpenAiModel(Model):
    def __init__(self, model_name):
        super().__init__(model_name)

        # HACK: Use EAST US 2 for gpt-5.x until EAST US is enabled
        if model_name.startswith("gpt-5"):
            self.api_url = os.environ["AZURE_OPENAI_URL_EASTUS2"]
            self.api_key = os.environ["AZURE_OPENAI_KEY_EASTUS2"]
        else:
            self.api_url = os.environ["AZURE_OPENAI_URL"]
            self.api_key = os.environ["AZURE_OPENAI_KEY"]
        self.api_version = "2025-01-01-preview"
        self.client = AzureOpenAI(
            api_key=self.api_key,
            azure_endpoint=self.api_url,
            api_version=self.api_version)

    def get_response(self, messages):

        # Create the parameters
        params = {
            "model": self.model_name,
            "messages": messages,
            "top_p": 1.0,
            # "reasoning_effort": "medium"
        }

        # Don't set temperature on reasoning models
        if "gpt-5" not in self.model_name:
            params["temperature"] = 0.0

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

                # Get model version
                self.model_version = response.model

                # Get tokens
                cached_tokens = getattr(response.usage.prompt_tokens_details, "cached_tokens", 0)
                prompt_tokens = getattr(response.usage, "prompt_tokens", 0)
                reasoning_tokens = getattr(response.usage.completion_tokens_details, "reasoning_tokens", 0)
                completion_tokens = getattr(response.usage, "completion_tokens", 0)
                total_tokens = getattr(response.usage, "total_tokens", 0)

                # Update tokens
                self.update_tokens(
                    cached_tokens=cached_tokens,
                    input_tokens=prompt_tokens,
                    reasoning_tokens=reasoning_tokens,
                    output_tokens=completion_tokens,
                    total_tokens=total_tokens)

                return content
            except Exception as e:

                # Fail on content filter violations since retry won't work
                if "content_filter" in str(e) or "ResponsibleAIPolicyViolation" in str(e):
                    raise

                if attempts >= len(retries):
                    raise

                delay = retries[attempts]
                warn(f"Retrying LLM API call in {delay} seconds due to error: {e}")
                time.sleep(delay)
                self.wait_time += delay
                attempts += 1

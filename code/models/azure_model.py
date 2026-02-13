import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from models.model import Model
from warnings import warn
import time

class AzureModel(Model):
    def __init__(self, model_name):
        super().__init__(model_name)
        self.api_url = os.environ['AZURE_AI_URL']
        self.api_key = os.environ['AZURE_AI_KEY']
        self.api_version = "2025-01-01-preview"
        self.client = ChatCompletionsClient(
            endpoint=f"{self.api_url}models",
            credential=AzureKeyCredential(self.api_key),
            api_version="2024-05-01-preview")

    def get_response(self, messages):

        # Set retry variables
        retries = [10, 20, 30, 60, 180, 300, 600, 1200, 1200]  # wait before each retry
        attempts = 0

        while True:
            try:
                # Get the response
                response = self.client.complete(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.0)

                # Get the content
                content = response.choices[0].message.content

                # Handle empty response
                if content is None:
                    raise ValueError("Received empty response from LLM API.")

                # Accumulate tokens
                self.cached_tokens += 0
                self.input_tokens += response.usage.prompt_tokens
                self.reasoning_tokens += 0
                self.output_tokens += response.usage.completion_tokens
                self.total_tokens += response.usage.total_tokens

                return content
            except Exception as e:

                if attempts >= len(retries):
                    raise

                delay = retries[attempts]
                warn(f"Retrying LLM API call in {delay} seconds due to error: {e}")
                time.sleep(delay)
                self.wait_time += delay
                attempts += 1

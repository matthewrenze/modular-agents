import os
import time
import anthropic
from logs.console import warn
from models.model import Model

class ClaudeModel(Model):
    def __init__(self, model_name):
        super().__init__(model_name)
        self.api_key = os.environ['ANTHROPIC_KEY']
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def get_response(self, messages):

        # Replace the system role with user role for Anthropic
        for message in messages:
            if message['role'] == 'system':
                message['role'] = 'user'
            if message["content"] == "":
                message["content"] = "[empty]"

        # Set retry variables
        retries = [10, 20, 30, 60, 180, 300, 600, 1200, 1200]  # wait before each retry
        attempts = 0

        while True:
            try:

                # Get the response
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=4096,
                    extra_body={"cache_control": {"type": "ephemeral"}},
                    messages=messages)

                # Get the content (if it exists)
                if response.content:
                    content = response.content[0].text
                else:
                    content = ""

                # Get model version
                self.model_version = response.model

                # Accumulate tokens
                usage = response.usage
                cached_tokens = usage.cache_read_input_tokens or 0
                cache_creation_tokens = usage.cache_creation_input_tokens or 0
                prompt_tokens = usage.input_tokens or 0
                input_tokens = prompt_tokens + cache_creation_tokens
                output_tokens = usage.output_tokens or 0
                total_tokens = cached_tokens + input_tokens + output_tokens

                # Update tokens
                self.update_tokens(
                    cached_tokens=cached_tokens,
                    input_tokens=input_tokens,
                    reasoning_tokens=0,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens)

                return content

            except Exception as e:

                if attempts >= len(retries):
                    raise

                delay = retries[attempts]
                warn(f"Retrying LLM API call in {delay} seconds due to error: {e}")
                self.wait_time += delay
                time.sleep(delay)
                attempts += 1
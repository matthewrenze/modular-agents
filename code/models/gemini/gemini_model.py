import os
import time
from google import genai
from logs.console import warn
from models.model import Model

class GeminiModel(Model):
    def __init__(self, model_name):
        super().__init__(model_name)
        self.api_key = os.environ["GOOGLE_API_KEY"]
        self.client = genai.Client(api_key=self.api_key)

    def get_response(self, messages):

        # Copy the messages
        messages = [message.copy() for message in messages]
        
        # Format messages for Gemini
        for message in messages:
            if message["role"] == "system":
                message["role"] = "user"
            if message["role"] == "assistant":
                message["role"] = "model"
            if "parts" not in message:
                message["parts"] = [{"text": message["content"]}]
                del message["content"]

        # Set retry variables
        retries = [10, 20, 30, 60, 180, 300, 600, 1200, 1200]  # wait before each retry
        attempts = 0

        while True:
            try:

                # Get the response
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=messages,
                )

                # Get the content
                # content = response.text

                # Hack to prevent the "non-text parts in response" warning
                # And hack to set STOP token (without empty string) to empty string
                # Thinking models may return a thought part first, so join the
                # non-thought text parts instead of assuming parts[0] is the text
                parts = response.candidates[0].content.parts
                if parts is not None:
                    content = "".join(part.text for part in parts
                                      if part.text and not part.thought)
                else:
                    content = ""

                # Get model version
                self.model_version = response.model_version

                # Get tokens
                usage = response.usage_metadata
                cached_tokens = usage.cached_content_token_count or 0
                prompt_tokens = usage.prompt_token_count or 0
                input_tokens = prompt_tokens - cached_tokens
                reasoning_tokens = usage.thoughts_token_count or 0
                output_tokens = usage.candidates_token_count or 0
                total_tokens = usage.total_token_count or 0

                # Update tokens
                self.update_tokens(
                    cached_tokens=cached_tokens,
                    input_tokens=input_tokens,
                    reasoning_tokens=reasoning_tokens,
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

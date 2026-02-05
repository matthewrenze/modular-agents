import os
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference import ChatCompletionsClient
from models.model import Model

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

        # Get the response
        response = self.client.complete(
            model=self.model_name,
            messages=messages,
            temperature=0.0)

        # Get the content
        content = response.choices[0].message.content

        # Accumulate tokens
        self.input_tokens += response.usage.prompt_tokens
        self.output_tokens += response.usage.completion_tokens
        self.total_tokens += response.usage.total_tokens

        return content

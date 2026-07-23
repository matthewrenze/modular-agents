from models.model import Model
from models.azure_openai.azure_openai_model import AzureOpenAiModel
from models.openai.openai_model import OpenAiModel
from params.parameters import Parameters
from models.claude.claude_model import ClaudeModel
from models.azure.azure_model import AzureModel
from models.gemini.gemini_model import GeminiModel
from models.fireworks.fireworks_model import FireworksModel

class ModelFactory():

    def create(self, params: Parameters, use_azure: bool) -> Model:

        if params.model_name.startswith("claude"):
            return ClaudeModel(params.model_name)

        elif params.model_name.startswith("deepseek"):
            return FireworksModel(params.model_name)

        elif params.model_name.startswith("gemini"):
            return GeminiModel(params.model_name)

        elif params.model_name.startswith("gpt"):
            if use_azure:
                return AzureOpenAiModel(params.model_name)
            else:
                return OpenAiModel(params.model_name)

        elif params.model_name.startswith("kimi"):
            return FireworksModel(params.model_name)

        elif params.model_name.startswith("glm"):
            return FireworksModel(params.model_name)

        elif params.model_name.startswith("minimax"):
            return FireworksModel(params.model_name)

        elif params.model_name.startswith("nemotron"):
            return FireworksModel(params.model_name)

        else:
            raise ValueError(f"Unknown model name: {params.model_name}")
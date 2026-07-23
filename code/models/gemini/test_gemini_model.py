from types import SimpleNamespace
from google import genai
from models.gemini.gemini_model import GeminiModel

def create_fake_response(parts):
    return SimpleNamespace(
        candidates=[SimpleNamespace(content=SimpleNamespace(parts=parts))],
        model_version="gemini-3.1-pro-preview",
        usage_metadata=SimpleNamespace(
            cached_content_token_count=0,
            prompt_token_count=10,
            thoughts_token_count=0,
            candidates_token_count=5,
            total_token_count=15))

def create_fake_client(response):
    def generate_content(**kwargs):
        return response
    return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))

class TestGeminiModel:

    def create_model(self, monkeypatch, response):
        monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
        monkeypatch.setattr(genai, "Client", lambda api_key: create_fake_client(response))
        return GeminiModel("gemini-3.1-pro-preview")

    def test_text_part_only(self, monkeypatch):
        response = create_fake_response([SimpleNamespace(text="pong", thought=None)])
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == "pong"

    def test_thought_part_before_text_part(self, monkeypatch):
        response = create_fake_response([
            SimpleNamespace(text=None, thought=True),
            SimpleNamespace(text="pong", thought=None)])
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == "pong"

    def test_none_parts(self, monkeypatch):
        response = create_fake_response(None)
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == ""

    def test_thought_parts_only(self, monkeypatch):
        response = create_fake_response([SimpleNamespace(text=None, thought=True)])
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == ""

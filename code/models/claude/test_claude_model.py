from types import SimpleNamespace
import anthropic
from models.claude.claude_model import ClaudeModel

def create_fake_response(content):
    return SimpleNamespace(
        content=content,
        model="claude-fable-5",
        usage=SimpleNamespace(
            cache_read_input_tokens=0,
            cache_creation_input_tokens=0,
            input_tokens=10,
            output_tokens=5))

def create_fake_client(response):
    messages = SimpleNamespace(create=lambda **kwargs: response)
    return SimpleNamespace(messages=messages)

class TestClaudeModel:

    def create_model(self, monkeypatch, response):
        monkeypatch.setenv("ANTHROPIC_KEY", "test-key")
        monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: create_fake_client(response))
        return ClaudeModel("claude-fable-5")

    def test_text_block_only(self, monkeypatch):
        response = create_fake_response([SimpleNamespace(type="text", text="pong")])
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == "pong"

    def test_thinking_block_before_text_block(self, monkeypatch):
        response = create_fake_response([
            SimpleNamespace(type="thinking", thinking=""),
            SimpleNamespace(type="text", text="pong")])
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == "pong"

    def test_empty_content(self, monkeypatch):
        response = create_fake_response([])
        model = self.create_model(monkeypatch, response)
        content = model.get_response([{"role": "user", "content": "ping"}])
        assert content == ""

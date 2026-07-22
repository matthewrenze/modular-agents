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

def create_fake_client(response, captured_kwargs=None):
    def create(**kwargs):
        if captured_kwargs is not None:
            captured_kwargs.update(kwargs)
        return response
    return SimpleNamespace(messages=SimpleNamespace(create=create))

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

    def test_default_max_tokens(self, monkeypatch):
        response = create_fake_response([SimpleNamespace(type="text", text="pong")])
        captured_kwargs = {}
        monkeypatch.setenv("ANTHROPIC_KEY", "test-key")
        monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: create_fake_client(response, captured_kwargs))
        model = ClaudeModel("claude-fable-5")
        model.get_response([{"role": "user", "content": "ping"}])
        assert captured_kwargs["max_tokens"] == 4096

    def test_explicit_timeout_allows_large_max_tokens(self, monkeypatch):
        # Without an explicit timeout the SDK rejects non-streaming calls whose max_tokens
        # implies >10 minutes ("Streaming is required..."), so large budgets need it passed
        response = create_fake_response([SimpleNamespace(type="text", text="pong")])
        captured_kwargs = {}
        monkeypatch.setenv("ANTHROPIC_KEY", "test-key")
        monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: create_fake_client(response, captured_kwargs))
        model = ClaudeModel("claude-fable-5")
        model.get_response([{"role": "user", "content": "ping"}])
        assert captured_kwargs["timeout"] == 3600.0

    def test_timeout_override(self, monkeypatch):
        response = create_fake_response([SimpleNamespace(type="text", text="pong")])
        captured_kwargs = {}
        monkeypatch.setenv("ANTHROPIC_KEY", "test-key")
        monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: create_fake_client(response, captured_kwargs))
        model = ClaudeModel("claude-fable-5")
        model.timeout = 1200.0
        model.get_response([{"role": "user", "content": "ping"}])
        assert captured_kwargs["timeout"] == 1200.0

    def test_max_tokens_override(self, monkeypatch):
        response = create_fake_response([SimpleNamespace(type="text", text="pong")])
        captured_kwargs = {}
        monkeypatch.setenv("ANTHROPIC_KEY", "test-key")
        monkeypatch.setattr(anthropic, "Anthropic", lambda api_key: create_fake_client(response, captured_kwargs))
        model = ClaudeModel("claude-fable-5")
        model.max_tokens = 16384
        model.get_response([{"role": "user", "content": "ping"}])
        assert captured_kwargs["max_tokens"] == 16384

import os
from params.parameters_factory import ParametersFactory
from prompts.system_prompt_factory import SystemPromptFactory
import generate_prompt_samples
from generate_prompt_samples import create_sample, subagents

class TestGeneratePromptSamples:
    def test_create_sample_fills_template(self):
        sample = create_sample("react-kn", "react-kn")
        assert "{actions}" not in sample
        assert "{examples}" not in sample
        assert "{max_steps}" in sample

    def test_create_sample_matches_factory(self):
        params = ParametersFactory().create("test", "", "modular-full", "", "")
        params.max_steps = 99
        with open("agents/actor/actor-system-prompt.md", "r") as template_file:
            template = template_file.read()
        expected = SystemPromptFactory().create(params, "actor", template)
        sample = create_sample("actor", "modular-full")
        assert sample.replace("{max_steps}", "99") == expected

    def test_main_writes_all_samples(self, tmp_path, monkeypatch):
        monkeypatch.setattr(generate_prompt_samples, "output_folder", str(tmp_path))
        generate_prompt_samples.main()
        for subagent, _ in subagents:
            sample_path = tmp_path / f"{subagent}-system-prompt.md"
            assert sample_path.exists()
            assert "{max_steps}" in sample_path.read_text()

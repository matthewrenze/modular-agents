import os
from params.parameters_factory import ParametersFactory
from prompts.system_prompt_factory import SystemPromptFactory

# Set parameters
output_folder = "../docs/samples"
subagents = [
    ("react-kn", "react-kn"),
    ("summarizer", "modular-full"),
    ("memorizer", "modular-full"),
    ("planner", "modular-full"),
    ("reasoner", "modular-full"),
    ("actor", "modular-full"),
    ("modular-single", "modular-single")]

# NOTE: max_steps is set per episode at runtime, so the samples keep the
# literal {max_steps} placeholder; the sentinel survives factory replacement.
max_steps_sentinel = 987654321


def create_sample(subagent: str, agent_name: str) -> str:

    # Create the parameters
    parameters_factory = ParametersFactory()
    params = parameters_factory.create("test", "", agent_name, "", "")
    params.max_steps = max_steps_sentinel

    # Load the system prompt template
    subagent_folder = subagent.replace("-", "_")
    template_path = f"agents/{subagent_folder}/{subagent}-system-prompt.md"
    with open(template_path, "r") as template_file:
        template = template_file.read()

    # Create the system prompt
    system_prompt_factory = SystemPromptFactory()
    system_prompt = system_prompt_factory.create(params, subagent, template)

    # Restore the max-steps placeholder
    return system_prompt.replace(str(max_steps_sentinel), "{max_steps}")


def main():

    # Create the output folder
    os.makedirs(output_folder, exist_ok=True)

    # Write each system prompt sample
    for subagent, agent_name in subagents:
        sample = create_sample(subagent, agent_name)
        sample_path = os.path.join(output_folder, f"{subagent}-system-prompt.md")
        with open(sample_path, "w") as sample_file:
            sample_file.write(sample)
        print(f"Wrote {sample_path}")


if __name__ == "__main__":
    main()

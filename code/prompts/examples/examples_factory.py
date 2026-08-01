import os
from params.parameters import Parameters

class ExamplesFactory:
    def create(self, params: Parameters, subagent: str):

        # The modular-single agent gets combined five-section examples
        if subagent == "modular-single":
            return self.create_modular_single(params)

        content = ""
        for step in range(1, 10):
            content += f"## Example {step}\n"

            # Add the note (if it exists)
            note = self.get_note(step)
            if note is not None:
                content += note

            content += "### Input\n"

            # Add the task to every step (except for react then only first step)
            if not subagent.startswith("react") \
                    or (subagent.startswith("react") and step == 1):
                content += self.get_part(0, "input-task")

            # Add the history (for everything except react)
            if params.use_summarizer and not subagent.startswith("react"):
                content += self.get_part(step, "input-history")

            # Add the previous memories (for the memorizer)
            if subagent == "memorizer" and params.use_memorizer:
                content += self.get_part(step, "input-memories")

            # Add the previous plan (for the planner only)
            if subagent == "planner" and params.use_planner:
                content += self.get_part(step, "input-plan")

            # Add previous environment (for the reasoner, actor, and planner)
            if subagent in ("reasoner", "actor", "planner") and step > 1:
                content += self.get_part(step - 1, "input-env")

            # Add the previous thought and action (for the reasoner, actor, and planner)
            if subagent in ("reasoner", "actor", "planner") and step > 1:
                content += "Agent:\n"
                if params.use_reasoner:
                    content += f"  Thought: {self.get_part(step - 1, 'output-thought')}"
                content += f"  Action: {self.get_part(step - 1, 'output-action')}"

            # Add the previous thought and action (for the summarizer and memorizer)
            if subagent in ("summarizer", "memorizer") and step > 1:
                content += f"Step: {step - 1} of 10\n"
                content += "Agent:\n"
                if params.use_reasoner:
                    content += f"  Thought: {self.get_part(step - 1, 'output-thought')}"
                content += f"  Action: {self.get_part(step - 1, 'output-action')}"

            # Add current environment
            content += self.get_part(step, "input-env")

            # Add the current thought (for the actor)
            if subagent == "actor" and params.use_reasoner:
                content += "Agent:\n"
                content += f"  Thought: {self.get_part(step, 'output-thought')}"

            # Add the current memories (for the actor and the reasoner)
            if subagent in ("planner", "reasoner", "actor") \
                    and params.use_memorizer:
                content += self.get_part(step + 1, "input-memories")

            # Add the updated plan (for the actor and reasoner)
            if subagent in ("actor", "reasoner") and params.use_planner:
                content += self.get_part(step + 1, "input-plan")

            content += "\n### Output\n"

            if subagent.startswith("react"):
                content += f"Thought: {self.get_part(step, 'output-thought')}"
                content += f"Action: {self.get_part(step, 'output-action')}"

            if subagent == "summarizer":
                content += self.get_part(step, "output-summary")

            if subagent == "memorizer":
                content += self.get_part(step, "output-memory")

            if subagent == "planner":
                content += self.get_part(step, "output-plan")

            if subagent == "reasoner":
                content += self.get_part(step, "output-thought")

            if subagent == "actor":
                content += self.get_part(step, "output-action")

            content += "\n"

        return content

    def create_modular_single(self, params: Parameters):
        content = ""
        for step in range(1, 10):
            content += f"## Example {step}\n"

            # Add the note (if it exists)
            note = self.get_note(step)
            if note is not None:
                content += note

            content += "### Input\n"

            # Add the task
            content += self.get_part(0, "input-task")

            # Add the history
            if params.use_summarizer:
                content += self.get_part(step, "input-history")

            # Add the previous memories (pre-update)
            if params.use_memorizer:
                content += self.get_part(step, "input-memories")

            # Add the previous plan (pre-update)
            if params.use_planner:
                content += self.get_part(step, "input-plan")

            # Add the previous environment, thought, and action
            if step > 1:
                content += self.get_part(step - 1, "input-env")
                content += "Agent:\n"
                if params.use_reasoner:
                    content += f"  Thought: {self.get_part(step - 1, 'output-thought')}"
                content += f"  Action: {self.get_part(step - 1, 'output-action')}"

            # Add the current environment
            content += self.get_part(step, "input-env")

            content += "\n### Output\n"

            # Add the five labeled sections in execution order
            if params.use_summarizer:
                content += "## Summary\n"
                content += self.get_part(step, "output-summary")
            if params.use_memorizer:
                content += "## Memory\n"
                content += self.get_part(step, "output-memory")
            if params.use_planner:
                content += "## Plan\n"
                content += self.get_part(step, "output-plan")
            if params.use_reasoner:
                content += "## Thought\n"
                content += self.get_part(step, "output-thought")
            content += "## Action\n"
            content += self.get_part(step, "output-action")

            content += "\n"

        return content

    @staticmethod
    def get_note(step: int) -> str | None:
        file_path = f"prompts/examples/step-{step}/{step}-note.md"
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r") as file:
            return file.read() + "\n"

    @staticmethod
    def get_part(step: int, part: str) -> str:
        file_path = f"prompts/examples/step-{step}/{step}-{part}.md"
        with open(file_path, "r") as file:
            return file.read() + "\n"
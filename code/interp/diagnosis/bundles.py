from interp.episode_extract import EpisodeExtract

MODULE_ORDER = ["summarizer", "memorizer", "planner", "reasoner", "actor", "react"]

# Size caps (chars), sized at ~2x the p99 of normal field lengths so they bind only on
# pathological artifact dumps (decisions section 60-62); measured over all 259 failure bundles
FIELD_CAP = 4000     # each step field: summary, thought, action, plan/memory snapshot
FINAL_CAP = 30000    # final plan; final memories block
MESSAGE_CAP = 30000  # each raw module message

def truncate(text: str, cap: int) -> str:
    # Keep head + tail with an explicit marker: the marker itself preserves the dump signal
    if len(text) <= cap:
        return text
    half = cap // 2
    return f"{text[:half]}\n[... truncated {len(text) - cap} chars ...]\n{text[-half:]}"

class LabelerBundleRenderer:
    """Renders the full-data input bundle for the pre-labeler/labeler roles (protocol section 4)."""

    def render(self, extract: EpisodeExtract, solution: list, outcome: dict) -> str:
        sections = [self.render_header(extract, outcome),
                    self.render_task(extract, solution),
                    self.render_final_artifacts(extract),
                    self.render_steps(extract),
                    self.render_messages(extract)]
        return "\n\n".join(section for section in sections if section)

    def render_header(self, extract: EpisodeExtract, outcome: dict) -> str:
        params = extract.params
        return "\n".join([
            "=== EPISODE ===",
            f"Model: {params.model_name}",
            f"Agent: {params.agent_name}",
            f"Eval: {params.eval_name} (episode {params.episode_id})",
            f"Outcome: success = {outcome['success']}, score = {outcome['score']}/{outcome['max_score']}, "
            f"steps = {outcome['steps']}/{outcome['max_steps']}, max_steps_hit = {outcome['max_steps_hit']}"])

    def render_task(self, extract: EpisodeExtract, solution: list) -> str:
        return "\n".join([
            "=== TASK ===",
            extract.state.task_state.task,
            "",
            "=== GROUND-TRUTH SOLUTION ===",
            ", ".join(solution)])

    def render_final_artifacts(self, extract: EpisodeExtract) -> str:
        # Final plan/memories exist for modular agents only; skip the sections when absent
        sections = []
        if extract.state.plan.strip():
            sections.append(f"=== FINAL PLAN ===\n{truncate(extract.state.plan, FINAL_CAP)}")
        if extract.state.memories:
            memories = "\n".join(f"{key}: {value}" for key, value in extract.state.memories.items())
            sections.append(f"=== FINAL MEMORIES ===\n{truncate(memories, FINAL_CAP)}")
        return "\n\n".join(sections)

    def render_steps(self, extract: EpisodeExtract) -> str:
        # Acted-on steps are step_history[:-1]; the extra terminal entry is the episode outcome
        lines = ["=== STEP HISTORY ==="]
        prev_plan, prev_memory = "", ""
        for step in extract.state.step_history[:-1]:
            env_state, agent_state = step.env_state, step.agent_state
            lines.append(f"--- Step {step.step_id} ---")
            lines.append(f"Location: {env_state.location}")
            if env_state.inventory:
                lines.append(f"Inventory: {env_state.inventory}")
            lines.append(f"Score: {env_state.score}")
            if env_state.feedback:
                lines.append(f"Feedback: {env_state.feedback}")
            if agent_state.summary:
                lines.append(f"Summary: {truncate(agent_state.summary, FIELD_CAP)}")
            if agent_state.plan and agent_state.plan != prev_plan:
                lines.append(f"Plan:\n{truncate(agent_state.plan, FIELD_CAP)}")
            if agent_state.memory and agent_state.memory != prev_memory:
                lines.append(f"Memory:\n{truncate(agent_state.memory, FIELD_CAP)}")
            if agent_state.thought:
                lines.append(f"Thought: {truncate(agent_state.thought, FIELD_CAP)}")
            lines.append(f"Action: {truncate(agent_state.action, FIELD_CAP)}")
            lines.append("")
            prev_plan, prev_memory = agent_state.plan, agent_state.memory
        terminal = extract.state.step_history[-1].env_state
        lines.append("--- Episode outcome ---")
        if terminal.feedback:
            lines.append(f"Feedback: {terminal.feedback}")
        lines.append(f"Done: {terminal.is_done}")
        return "\n".join(lines)

    def render_messages(self, extract: EpisodeExtract) -> str:
        if not extract.last_messages:
            return ""
        lines = [f"=== RAW MODULE MESSAGES (LAST {len(extract.last_messages)} STEPS) ==="]
        for step_id in sorted(extract.last_messages):
            modules = extract.last_messages[step_id]
            for module in sorted(modules, key=lambda name: (MODULE_ORDER.index(name)
                                                            if name in MODULE_ORDER else len(MODULE_ORDER), name)):
                lines.append(f"--- Step {step_id} - {module} ---")
                lines.append(truncate(modules[module].strip(), MESSAGE_CAP))
        return "\n".join(lines)

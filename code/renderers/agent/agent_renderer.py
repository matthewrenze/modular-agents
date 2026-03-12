from states.agent_state import AgentState

class AgentRenderer:

    def render(self, agent_state: AgentState, log_mode: bool = False) -> str:
        result = f"Agent:\n" \

        if agent_state.summary != "" and log_mode:
            result += f"  Summary: {agent_state.summary}\n"

        if agent_state.memory != "" and log_mode:
            memory = self.render_memory_updates(agent_state.memory)
            result += f"  Memory:\n{memory}\n"

        if agent_state.plan != "" and log_mode:
            plan = self.render_plan_updates(agent_state.plan)
            result += f"  Plan:\n{plan}\n"

        if agent_state.thought != "":
            result += f"  Thought: {agent_state.thought}\n" \

        if agent_state.action != "":
            result += f"  Action: {agent_state.action}\n" \

        return result

    def render_plan_updates(self, plan: str) -> str:
        plan = plan.replace("NO_CHANGE", "    NO_CHANGE")
        plan = plan.replace("- [", "    - [")
        return plan

    def render_memory_updates(self, memory: str) -> str:
        return "\n".join([f"    {line}" for line in memory.splitlines()])
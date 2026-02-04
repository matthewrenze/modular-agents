from states.agent_state import AgentState

class AgentRenderer:

    def render(self, agent_state: AgentState):
        result = f"Agent:\n" \

        if agent_state.summary != "":
            result += f"  Summary: {agent_state.summary}\n"

        if agent_state.memory != "":
            memory = self.render_memory_items(agent_state.memory)
            result += f"  Memory:\n{memory}\n"

        if agent_state.thought != "":
            result += f"  Thought: {agent_state.thought}\n" \

        if agent_state.action != "":
            result += f"  Action: {agent_state.action}\n" \

        return result

    def render_memory_items(self, memory: str) -> str:
        memory = memory.replace("create:", "    create:")
        memory = memory.replace("delete:", "    delete:")
        return memory
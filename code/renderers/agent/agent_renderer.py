from states.agent_state import AgentState

class AgentRenderer:

    def render(self, agent_state: AgentState):
        result = f"Agent:\n" \

        if agent_state.summary != "":
            result += f"  Summary: {agent_state.summary}\n"

        if agent_state.plan != "":
            plan = self.render_plan_updates(agent_state.plan)
            result += f"  Plan:\n{plan}\n"

        if agent_state.memory != "":
            memory = self.render_memory_updates(agent_state.memory)
            result += f"  Memory:\n{memory}\n"

        if agent_state.thought != "":
            result += f"  Thought: {agent_state.thought}\n" \

        if agent_state.action != "":
            result += f"  Action: {agent_state.action}\n" \

        return result

    def render_plan_updates(self, plan: str) -> str:
        plan = plan.replace("add:", "    add:")
        plan = plan.replace("insert:", "    insert:")
        plan = plan.replace("update:", "    update:")
        plan = plan.replace("mark:", "    mark:")
        plan = plan.replace("delete:", "    delete:")
        return plan

    def render_memory_updates(self, memory: str) -> str:
        memory = memory.replace("create:", "    create:")
        memory = memory.replace("delete:", "    delete:")
        return memory
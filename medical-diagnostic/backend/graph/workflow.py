from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from backend.graph.state import MedicalState
from backend.agents.supervisor import supervisor_node
from backend.agents.diagnostic_agent import diagnostic_agent_node
from backend.agents.physician_review import physician_review_node
from backend.agents.report_agent import report_agent_node

def build_workflow():
    workflow = StateGraph(MedicalState)

    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("diagnostic_agent", diagnostic_agent_node)
    workflow.add_node("physician_review", physician_review_node)
    workflow.add_node("report_agent", report_agent_node)

    workflow.add_edge(START, "supervisor")
    workflow.add_edge("supervisor", "diagnostic_agent")
    workflow.add_edge("supervisor", "physician_review")
    workflow.add_edge("supervisor", "report_agent")
    workflow.add_edge("supervisor", END)

    # Arêtes conditionnelles basées sur le champ "next" retourné par chaque nœud
    def route_after_diagnostic(state):
        return state.get("next", "supervisor")
    def route_after_physician(state):
        return state.get("next", "supervisor")
    def route_after_report(state):
        return state.get("next", "supervisor")

    workflow.add_conditional_edges("diagnostic_agent", route_after_diagnostic)
    workflow.add_conditional_edges("physician_review", route_after_physician)
    workflow.add_conditional_edges("report_agent", route_after_report)

    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    return app
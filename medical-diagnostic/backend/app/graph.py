from langgraph.graph import StateGraph, END

from app.nodes.diagnostic_agent import diagnostic_agent
from app.nodes.physician_review import physician_review
from app.nodes.report_agent import report_agent
from app.state import MedicalState


builder = StateGraph(MedicalState)

builder.add_node("diagnostic_agent", diagnostic_agent)
builder.add_node("physician_review", physician_review)
builder.add_node("report_agent", report_agent)

builder.set_entry_point("diagnostic_agent")

builder.add_edge("diagnostic_agent", "physician_review")
builder.add_edge("physician_review", "report_agent")
builder.add_edge("report_agent", END)

graph = builder.compile()
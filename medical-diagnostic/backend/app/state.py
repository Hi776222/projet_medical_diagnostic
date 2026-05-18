from typing import Annotated
from typing_extensions import TypedDict, Literal
from langgraph.graph.message import add_messages


class MedicalState(TypedDict, total=False):

    messages: Annotated[list, add_messages]

    next: Literal[
        "diagnostic_agent",
        "physician_review",
        "report_agent",
        "FINISH"
    ]

    patient_case: str

    question_count: int

    patient_answers: list

    current_question: str

    diagnostic_summary: str

    interim_care: str

    physician_treatment: str

    final_report: str
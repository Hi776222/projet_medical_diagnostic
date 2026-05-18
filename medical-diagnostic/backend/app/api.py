from fastapi import FastAPI
from pydantic import BaseModel

from app.graph import graph

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "API running"}


class ConsultationRequest(BaseModel):
    patient_case: str


@app.post("/consultation/start")
async def start_consultation(data: ConsultationRequest):

    state = {
        "messages": [],
        "patient_case": data.patient_case,
        "question_count": 0,
        "patient_answers": [],
        "next": "diagnostic_agent"
    }

    try:
        result = graph.invoke(state)
        return result

    except Exception as e:
        return {"error": str(e)}
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uuid
from langgraph.types import Command
from backend.graph.workflow import build_workflow
from backend.graph.state import MedicalState

app = FastAPI()
graph = build_workflow()
threads: Dict[str, Any] = {}

class StartConsultationRequest(BaseModel):
    initial_case: str

class ResumeRequest(BaseModel):
    thread_id: str
    user_response: Optional[str] = None
    physician_treatment: Optional[str] = None

@app.post("/sessions/start")
def start_session():
    thread_id = str(uuid.uuid4())
    threads[thread_id] = {}
    return {"thread_id": thread_id}

@app.post("/consultation/start")
def start_consultation(req: StartConsultationRequest):
    thread_id = str(uuid.uuid4())
    initial_state = MedicalState(
        messages=[],
        next="diagnostic_agent",
        question_count=0,
        questions_asked=[],
        interim_care="",
        diagnostic_summary="",
        physician_treatment=None,
        final_report="",
        patient_initial_case=req.initial_case
    )
    config = {"configurable": {"thread_id": thread_id}}
    # Lancer le graphe et capturer la première interruption (s'il y en a)
    try:
        for _ in graph.stream(initial_state, config, stream_mode="values"):
            pass
    except Exception as e:
        # Les interruptions sont levées comme exceptions – nous les gérons dans /resume
        pass
    threads[thread_id] = {"config": config}
    return {"thread_id": thread_id}

@app.post("/consultation/resume")
def resume_consultation(req: ResumeRequest):
    if req.thread_id not in threads:
        raise HTTPException(400, "Thread invalide")
    config = threads[req.thread_id]["config"]
    state = graph.get_state(config)
    if not state or not state.tasks:
        raise HTTPException(400, "Pas d'interruption en cours")
    # Déterminer le type d'interruption à partir de la valeur
    interrupt_info = state.tasks[0].interrupts[0]
    if isinstance(interrupt_info.value, dict) and interrupt_info.value.get("type") == "physician_review":
        if req.physician_treatment is None:
            raise HTTPException(400, "Traitement médecin requis")
        resume_value = {"treatment": req.physician_treatment}
    else:
        if req.user_response is None:
            raise HTTPException(400, "Réponse patient requise")
        resume_value = req.user_response
    # Reprendre l'exécution
    for _ in graph.stream(Command(resume=resume_value), config, stream_mode="values"):
        pass
    final_state = graph.get_state(config)
    threads[req.thread_id]["state"] = final_state.values
    return {"status": "resumed", "thread_id": req.thread_id, "final_state": final_state.values}

@app.get("/consultation/{thread_id}")
def get_state(thread_id: str):
    if thread_id not in threads:
        raise HTTPException(404, "Thread non trouvé")
    state = graph.get_state(threads[thread_id]["config"])
    return {"state": state.values if state else None}

@app.get("/consultation/{thread_id}/report")
def get_report(thread_id: str):
    if thread_id not in threads:
        raise HTTPException(404, "Thread non trouvé")
    state = threads[thread_id].get("state", {})
    return {"report": state.get("final_report", "Rapport non disponible")}
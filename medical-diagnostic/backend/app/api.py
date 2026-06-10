from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import re

from app.graph import graph

app = FastAPI()

# ── Stockage en mémoire des threads ──────────────────────────────────────────
sessions: dict = {}


# ── Schemas ───────────────────────────────────────────────────────────────────
class ConsultationRequest(BaseModel):
    patient_case: str


class ResumeRequest(BaseModel):
    thread_id: str
    answer: Optional[str] = None
    question_number: Optional[int] = None
    physician_treatment: Optional[str] = None
    step: Optional[str] = None


# ── Helper : splitter les questions ──────────────────────────────────────────
def _split_questions(text: str) -> list[str]:
    """
    Découpe un texte contenant plusieurs questions en une liste de questions.
    Ex: "Depuis quand ? Avez-vous de la fièvre ? Avez-vous une toux ?"
    → ["Depuis quand ?", "Avez-vous de la fièvre ?", "Avez-vous une toux ?"]
    """
    # Séparer sur les ? suivis d'un espace ou fin de chaîne
    parts = re.split(r'\?\s+', text.strip())
    questions = []
    for part in parts:
        part = part.strip()
        if part:
            # Remettre le ? supprimé par le split
            if not part.endswith('?'):
                part += ' ?'
            questions.append(part)
    return questions if questions else [text]


def _extract_current_question(state: dict) -> str:
    """Extrait le texte brut de la question depuis le state."""
    if state.get("current_question"):
        return state["current_question"]

    messages = state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "type") and msg.type in ("ai", "assistant"):
            return msg.content
        if isinstance(msg, dict):
            role = msg.get("role", msg.get("type", ""))
            if role in ("ai", "assistant"):
                return msg.get("content", "")

    return "Question suivante..."


def _get_next_question(session: dict) -> str:
    """
    Retourne la prochaine question de la file.
    Si la file est vide, génère de nouvelles questions depuis le state.
    """
    queue = session.get("question_queue", [])
    if queue:
        return queue.pop(0)
    return None


def _load_queue_from_state(session: dict, state: dict):
    """Charge la file de questions depuis le state si elle est vide."""
    if not session.get("question_queue"):
        raw = _extract_current_question(state)
        questions = _split_questions(raw)
        session["question_queue"] = questions


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "API running"}


@app.post("/consultation/start")
async def start_consultation(data: ConsultationRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [],
        "patient_case": data.patient_case,
        "question_count": 0,
        "patient_answers": [],
        "next": "diagnostic_agent",
    }

    try:
        result = graph.invoke(initial_state, config)

        # Splitter les questions retournées par l'agent
        raw_question = _extract_current_question(result)
        all_questions = _split_questions(raw_question)

        # Première question à afficher, le reste en file d'attente
        first_question = all_questions[0]
        question_queue = all_questions[1:]  # questions restantes

        sessions[thread_id] = {
            "state":          result,
            "config":         config,
            "patient_case":   data.patient_case,
            "question_queue": question_queue,   # ← file d'attente
        }

        return {
            "thread_id":      thread_id,
            "status":         "in_progress",
            "question":       first_question,
            "question_count": result.get("question_count", 1),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/consultation/resume")
async def resume_consultation(data: ResumeRequest):
    thread_id = data.thread_id
    session = sessions.get(thread_id)

    if not session:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' introuvable.")

    config = session["config"]

    try:
        # ── Cas 1 : réponse patient ───────────────────────────────────────────
        if data.answer is not None:
            current_state = session["state"]
            answers = list(current_state.get("patient_answers", []))
            answers.append(data.answer)
            q_count = data.question_number or len(answers)

            # Y a-t-il encore des questions en file d'attente ?
            queue = session.get("question_queue", [])

            if queue:
                # Servir la prochaine question de la file SANS rappeler le graph
                next_question = queue.pop(0)
                session["question_queue"] = queue
                session["state"] = {**current_state, "patient_answers": answers, "question_count": q_count}

                # Si c'était la 5e question, passer au médecin
                if q_count >= 5:
                    return {
                        "thread_id":          thread_id,
                        "next":               "physician_review",
                        "status":             "physician_review",
                        "diagnostic_summary": current_state.get("diagnostic_summary", ""),
                        "interim_care":       current_state.get("interim_care", ""),
                        "question_count":     q_count,
                    }

                return {
                    "thread_id":      thread_id,
                    "next":           "question",
                    "status":         "in_progress",
                    "question":       next_question,
                    "question_count": q_count,
                }

            else:
                # File vide → invoquer le graph pour obtenir de nouvelles questions
                update = {
                    **current_state,
                    "patient_answers": answers,
                    "question_count":  q_count,
                    "last_answer":     data.answer,
                }

                result = graph.invoke(update, config)
                sessions[thread_id]["state"] = result

                next_node = result.get("next", "")
                q_count   = result.get("question_count", q_count)

                if next_node == "physician_review" or q_count >= 5:
                    return {
                        "thread_id":          thread_id,
                        "next":               "physician_review",
                        "status":             "physician_review",
                        "diagnostic_summary": result.get("diagnostic_summary", ""),
                        "interim_care":       result.get("interim_care", ""),
                        "question_count":     q_count,
                    }

                # Splitter les nouvelles questions
                raw = _extract_current_question(result)
                all_questions = _split_questions(raw)
                first_question = all_questions[0]
                session["question_queue"] = all_questions[1:]

                return {
                    "thread_id":      thread_id,
                    "next":           "question",
                    "status":         "in_progress",
                    "question":       first_question,
                    "question_count": q_count,
                }

        # ── Cas 2 : validation médecin ────────────────────────────────────────
        elif data.physician_treatment is not None:
            current_state = session["state"]

            update = {
                **current_state,
                "physician_treatment": data.physician_treatment,
                "next": "report_agent",
            }

            result = graph.invoke(update, config)
            sessions[thread_id]["state"] = result

            return {
                "thread_id":    thread_id,
                "next":         "FINISH",
                "status":       "done",
                "final_report": result.get("final_report", ""),
            }

        else:
            raise HTTPException(
                status_code=400,
                detail="Fournir 'answer' ou 'physician_treatment'."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consultation/{thread_id}")
async def get_consultation(thread_id: str):
    session = sessions.get(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Thread introuvable.")
    state = session["state"]
    return {
        "thread_id":          thread_id,
        "status":             state.get("next", "unknown"),
        "question_count":     state.get("question_count", 0),
        "diagnostic_summary": state.get("diagnostic_summary", ""),
        "interim_care":       state.get("interim_care", ""),
        "patient_case":       session.get("patient_case", ""),
    }


@app.get("/consultation/{thread_id}/report")
async def get_report(thread_id: str):
    session = sessions.get(thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Thread introuvable.")
    state = session["state"]
    return {
        "thread_id":           thread_id,
        "patient_case":        session.get("patient_case", ""),
        "diagnostic_summary":  state.get("diagnostic_summary", ""),
        "interim_care":        state.get("interim_care", ""),
        "physician_treatment": state.get("physician_treatment", ""),
        "final_report":        state.get("final_report", ""),
    }
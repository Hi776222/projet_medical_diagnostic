import streamlit as st
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Système d'Orientation Clinique",
    page_icon="🩺",
    layout="centered",
)

st.markdown("""
<style>
    .q-bubble {
        background: #f0f6ff; border-left: 3px solid #185fa5;
        border-radius: 0 8px 8px 0; padding: 12px 16px;
        margin-bottom: 10px; font-size: 15px; color: #111;
    }
    .q-label { font-size: 11px; color: #185fa5; font-weight: 600; margin-bottom: 4px; }
    .a-bubble {
        background: #f8f9fa; border: 1px solid #dee2e6;
        border-radius: 8px; padding: 10px 14px;
        font-size: 14px; color: #5c6270; margin-bottom: 12px;
    }
    .summary-box {
        background: #f8f9fa; border-radius: 8px;
        padding: 14px; font-size: 14px; line-height: 1.7; color: #444;
    }
    .report-label {
        font-size: 11px; font-weight: 600; letter-spacing: 0.07em;
        text-transform: uppercase; color: #9199a8; margin-bottom: 4px;
    }
    .disclaimer {
        background: #faeeda; border: 1px solid #fac775;
        border-radius: 8px; padding: 12px 16px;
        font-size: 13px; color: #854f0b; margin-top: 14px;
    }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────────
DEFAULTS = {
    "screen": 1,
    "thread_id": None,
    "patient_case": "",
    "current_q": 1,
    "current_q_text": "",
    "qa_history": [],
    "diagnostic_summary": "",
    "interim_care": "",
    "physician_treatment": "",
    "final_report": "",
    "error_msg": "",
    "waiting_for_answer": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helpers ────────────────────────────────────────────────────────────────────
def safe_post(path, payload):
    try:
        r = requests.post(f"{BASE_URL}{path}", json=payload, timeout=15)
        if r.ok:
            return r.json(), None
        return None, f"HTTP {r.status_code}: {r.text[:200]}"
    except Exception as e:
        return None, str(e)

def safe_get(path):
    try:
        r = requests.get(f"{BASE_URL}{path}", timeout=15)
        if r.ok:
            return r.json(), None
        return None, f"HTTP {r.status_code}"
    except Exception as e:
        return None, str(e)

def render_stepper(current):
    labels = ["1 · Cas patient", "2 · Questions", "3 · Médecin", "4 · Rapport"]
    cols = st.columns(4)
    for i, (col, label) in enumerate(zip(cols, labels), start=1):
        with col:
            if i == current:
                st.markdown(f"**:blue[{label}]**")
            elif i < current:
                st.markdown(f"~~{label}~~ ✅")
            else:
                st.markdown(f"<span style='color:#ccc'>{label}</span>", unsafe_allow_html=True)
    st.divider()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 1 — Cas patient
# ══════════════════════════════════════════════════════════════════════════════
def screen_case():
    st.markdown("## 🩺 Système d'Orientation Clinique")
    st.caption("Exercice académique — ne remplace pas une consultation médicale")
    render_stepper(1)

    case = st.text_area(
        "📋 Description du cas initial",
        placeholder="Ex : Patient de 34 ans, fièvre depuis 3 jours (39 °C), toux sèche, fatigue importante...",
        height=160,
        key="input_case",
    )

    with st.expander("⚙️ Configuration API"):
        global BASE_URL
        BASE_URL = st.text_input("URL du backend FastAPI", value=BASE_URL, key="api_url")

    if st.session_state.error_msg:
        st.error(st.session_state.error_msg)

    if st.button("▶️ Démarrer la consultation", type="primary", use_container_width=True):
        if not case.strip():
            st.warning("Veuillez décrire le cas patient.")
            return

        with st.spinner("Démarrage..."):
            data, err = safe_post("/consultation/start", {"patient_case": case.strip()})

        if err or data is None:
            st.error(f"Erreur backend : {err}")
            return

        st.session_state.patient_case   = case.strip()
        st.session_state.thread_id      = data.get("thread_id", "unknown")
        st.session_state.current_q      = 1
        st.session_state.current_q_text = (
            data.get("question")
            or data.get("current_question")
            or "Quel est votre principal symptôme ?"
        )
        st.session_state.qa_history     = []
        st.session_state.error_msg      = ""
        st.session_state.screen         = 2
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 2 — Questions / Réponses (une seule question à la fois)
# ══════════════════════════════════════════════════════════════════════════════
def screen_questions():
    st.markdown("## 💬 Questions du diagnostic")
    render_stepper(2)

    q_num     = st.session_state.current_q
    q_text    = st.session_state.current_q_text
    thread_id = st.session_state.thread_id

    st.caption(f"thread: `{thread_id}`")
    st.progress(q_num / 5, text=f"Question {q_num} / 5")

    # ── Affichage de la question courante uniquement ──
    st.markdown(
        f'<div class="q-bubble"><div class="q-label">Question {q_num} sur 5</div>{q_text}</div>',
        unsafe_allow_html=True,
    )

    # ── Saisie de la réponse ──
    answer = st.text_input(
        "Votre réponse",
        key=f"ans_{q_num}",
        placeholder="Tapez votre réponse ici...",
        label_visibility="collapsed",
    )

    if st.session_state.error_msg:
        st.error(st.session_state.error_msg)

    col1, col2 = st.columns([4, 1])
    with col1:
        send = st.button("📤 Envoyer la réponse", type="primary", use_container_width=True)
    with col2:
        if st.button("↩️", help="Recommencer", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    if not send:
        return

    if not answer.strip():
        st.warning("Veuillez saisir une réponse.")
        return

    with st.spinner("Envoi..."):
        data, err = safe_post("/consultation/resume", {
            "thread_id":       thread_id,
            "answer":          answer.strip(),
            "question_number": q_num,
        })

    if err or data is None:
        st.session_state.error_msg = f"Erreur backend : {err}"
        st.rerun()
        return

    # Sauvegarder la réponse dans l'historique
    st.session_state.qa_history.append((q_text, answer.strip()))
    st.session_state.error_msg = ""

    next_step = data.get("next") or data.get("status") or ""

    if next_step == "physician_review" or q_num >= 5:
        st.session_state.diagnostic_summary = (
            data.get("diagnostic_summary") or data.get("summary") or ""
        )
        st.session_state.interim_care = (
            data.get("interim_care") or data.get("recommendation") or ""
        )
        st.session_state.screen = 3
        st.rerun()
    else:
        next_q = (
            data.get("question")
            or data.get("current_question")
            or f"Question {q_num + 1}"
        )
        st.session_state.current_q      = q_num + 1
        st.session_state.current_q_text = next_q
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 3 — Revue médecin (Human-in-the-Loop)
# ══════════════════════════════════════════════════════════════════════════════
def screen_physician():
    st.markdown("## 👨‍⚕️ Revue du médecin traitant")
    render_stepper(3)

    st.warning("⏳ Validation humaine requise avant la génération du rapport.", icon="⚠️")
    st.caption(f"thread: `{st.session_state.thread_id}`")

    st.markdown("**Synthèse clinique préliminaire**")
    st.markdown(
        f'<div class="summary-box">{st.session_state.diagnostic_summary or "Non disponible."}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    st.markdown("**Recommandation intermédiaire**")
    st.markdown(
        f'<div class="summary-box">{st.session_state.interim_care or "Non disponible."}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    treatment = st.text_area(
        "💊 Traitement / conduite à tenir (saisie médecin)",
        placeholder="Ex : Repos, paracétamol 1g/8h, hydratation 2L/j. Consulter si aggravation...",
        height=120,
        key="physician_input",
    )

    if st.session_state.error_msg:
        st.error(st.session_state.error_msg)

    col1, col2 = st.columns([4, 1])
    with col1:
        validate = st.button("✅ Valider et générer le rapport", type="primary", use_container_width=True)
    with col2:
        if st.button("↩️", help="Retour questions", use_container_width=True):
            st.session_state.screen = 2
            st.rerun()

    if not validate:
        return

    if not treatment.strip():
        st.warning("Veuillez saisir le traitement.")
        return

    with st.spinner("Génération du rapport..."):
        data, err = safe_post("/consultation/resume", {
            "thread_id":           st.session_state.thread_id,
            "physician_treatment": treatment.strip(),
            "step":                "physician_review",
        })

    if err or data is None:
        st.session_state.error_msg = f"Erreur backend : {err}"
        st.rerun()
        return

    st.session_state.physician_treatment = treatment.strip()
    st.session_state.final_report        = data.get("final_report") or data.get("report") or ""
    st.session_state.error_msg           = ""
    st.session_state.screen              = 4
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SCREEN 4 — Rapport final
# ══════════════════════════════════════════════════════════════════════════════
def screen_report():
    st.markdown("## 📋 Rapport Final")
    render_stepper(4)

    st.success("✅ Consultation terminée — rapport généré.")
    st.caption(f"thread: `{st.session_state.thread_id}`")

    # Si le rapport est vide, tenter de le récupérer
    if not st.session_state.final_report and st.session_state.thread_id:
        with st.spinner("Récupération du rapport..."):
            data, _ = safe_get(f"/consultation/{st.session_state.thread_id}/report")
        if data:
            st.session_state.final_report       = data.get("final_report", "")
            st.session_state.diagnostic_summary = data.get("diagnostic_summary", st.session_state.diagnostic_summary)
            st.session_state.interim_care       = data.get("interim_care", st.session_state.interim_care)

    def section(label, value):
        st.markdown(f'<div class="report-label">{label}</div>', unsafe_allow_html=True)
        st.write(value or "—")
        st.divider()

    section("Cas initial",                      st.session_state.patient_case)
    section("Synthèse clinique préliminaire",   st.session_state.diagnostic_summary)
    section("Recommandation intermédiaire",     st.session_state.interim_care)
    section("Prescription médecin traitant",    st.session_state.physician_treatment)
    section("Rapport final (agent)",            st.session_state.final_report)

    st.markdown(
        '<div class="disclaimer">⚠️ <strong>Ce système ne remplace pas une consultation médicale.</strong> '
        "Usage académique uniquement. Toute décision médicale doit être prise par un professionnel qualifié.</div>",
        unsafe_allow_html=True,
    )

    st.markdown("")
    col1, col2, col3 = st.columns(3)

    payload = {
        "thread_id":           st.session_state.thread_id,
        "patient_case":        st.session_state.patient_case,
        "diagnostic_summary":  st.session_state.diagnostic_summary,
        "interim_care":        st.session_state.interim_care,
        "physician_treatment": st.session_state.physician_treatment,
        "final_report":        st.session_state.final_report,
        "disclaimer":          "Ce système ne remplace pas une consultation médicale.",
    }

    with col1:
        st.download_button(
            label="⬇️ JSON",
            data=json.dumps(payload, ensure_ascii=False, indent=2),
            file_name=f"rapport_{st.session_state.thread_id or 'consultation'}.json",
            mime="application/json",
            use_container_width=True,
        )

    with col2:
        if st.button("🔄 Rafraîchir", use_container_width=True):
            data, _ = safe_get(f"/consultation/{st.session_state.thread_id}/report")
            if data:
                st.session_state.final_report = data.get("final_report", st.session_state.final_report)
            st.rerun()

    with col3:
        if st.button("🆕 Nouvelle consultation", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Router principal
# ══════════════════════════════════════════════════════════════════════════════
SCREENS = {1: screen_case, 2: screen_questions, 3: screen_physician, 4: screen_report}
SCREENS[st.session_state.screen]()
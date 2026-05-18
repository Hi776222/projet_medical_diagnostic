QUESTIONS = [
    "Depuis combien de temps avez-vous les symptômes ?",
    "Avez-vous de la fièvre ?",
    "Avez-vous des difficultés respiratoires ?",
    "Avez-vous des douleurs ?",
    "Prenez-vous actuellement des médicaments ?"
]


def ask_patient(state):
    count = state.get("question_count", 0)

    if count < len(QUESTIONS):
        return QUESTIONS[count]

    return None
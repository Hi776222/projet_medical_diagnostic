from langchain_core.messages import AIMessage

QUESTIONS = [
    "Depuis quand les symptômes ont-ils commencé ?",
    "Avez-vous de la fièvre ou des frissons ?",
    "Avez-vous une toux ?",
    "Avez-vous des difficultés respiratoires ?",
    "Avez-vous d'autres symptômes ?"
]

def diagnostic_agent(state):
    return {
        "messages": [
            AIMessage(content="\n".join(QUESTIONS))
        ],
        "next": "physician_review"
    }
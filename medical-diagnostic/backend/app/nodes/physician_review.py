def physician_review(state):
    return {
        "messages": state.get("messages", []),
        "physician_treatment": "OK"
    }
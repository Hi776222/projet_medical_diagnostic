def supervisor(state):
    return state.get("next", "diagnostic_agent")
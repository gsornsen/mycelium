# Source: wizard-integration.md
# Line: 758
# Valid syntax: True
# Has imports: True
# Has assignments: True

from fastapi import FastAPI, WebSocket

from mycelium_onboarding.wizard.flow import WizardFlow, WizardState

app = FastAPI()

# Store active wizard sessions
sessions = {}

@app.websocket("/ws/wizard/{session_id}")
async def wizard_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for interactive wizard."""
    await websocket.accept()

    # Create or resume session
    if session_id in sessions:
        state = sessions[session_id]
    else:
        state = WizardState()
        sessions[session_id] = state

    flow = WizardFlow(state)

    try:
        while not state.is_complete():
            # Send current step info
            await websocket.send_json({
                "step": state.current_step.value,
                "state": state.to_dict(),
            })

            # Receive user input
            data = await websocket.receive_json()

            # Process input based on current step
            # ... handle step logic ...

            # Advance
            flow.advance()

        # Send completion
        await websocket.send_json({"status": "complete"})

    except WebSocketDisconnect:
        # Save state for resume
        pass

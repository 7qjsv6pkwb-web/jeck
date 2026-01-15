from app.db.models import Action


def execute(action: Action) -> dict:
    return {
        "action_id": str(action.id),
        "type": action.type,
        "status": "executed",
    }

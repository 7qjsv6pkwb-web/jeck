git apply <<'EOF'
diff --git a/backend/app/api/v1/actions.py b/backend/app/api/v1/actions.py
index 3015ff02..c0ffee00 100644
--- a/backend/app/api/v1/actions.py
+++ b/backend/app/api/v1/actions.py
@@ -6,11 +6,12 @@ from sqlalchemy import select
 from sqlalchemy.orm import Session
 
 from app.db.models import Action, Thread
 from app.db.session import get_db_session
-from app.schemas.actions import ActionCreate, ActionResponse
+from app.schemas.actions import ActionApproveRequest, ActionCreate, ActionResponse
+from app.services import actions as actions_service
 
 router = APIRouter(tags=["actions"])
 
 
 @router.post(
@@ -21,27 +22,23 @@ router = APIRouter(tags=["actions"])
 def create_action(
     thread_id: UUID, payload: ActionCreate, db: Session = Depends(get_db_session)
 ) -> ActionResponse:
     thread = db.get(Thread, thread_id)
     if not thread:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found")
-    action = Action(
-        thread_id=thread_id,
-        type=payload.type,
-        policy_mode=payload.policy_mode,
-        status="DRAFT",
-        payload=payload.payload,
-        idempotency_key=payload.idempotency_key,
-    )
-    db.add(action)
+    action = actions_service.create_action(
+        db,
+        thread=thread,
+        action_type=payload.type,
+        policy_mode=payload.policy_mode,
+        payload=payload.payload,
+        idempotency_key=payload.idempotency_key,
+    )
     db.commit()
     db.refresh(action)
     return ActionResponse.model_validate(action)
EOF
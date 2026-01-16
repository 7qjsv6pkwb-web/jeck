import base64
from uuid import uuid4

from app.schemas.artifacts import ArtifactCreate
from app.services import artifacts as artifact_service


class _Stub:
    pass


def test_create_artifact_writes_file(tmp_path, monkeypatch):
    monkeypatch.setenv("ARTIFACTS_DIR", str(tmp_path))
    payload = ArtifactCreate(
        project_id=uuid4(),
        thread_id=uuid4(),
        action_id=uuid4(),
        type="text",
        filename="note.txt",
        metadata={"mime": "text/plain"},
        content_base64=base64.b64encode(b"hello").decode("ascii"),
    )

    db = _Stub()

    def fake_get(model, _id):
        return object()

    db.get = fake_get
    created = {}

    def fake_add(obj):
        created["artifact"] = obj

    db.add = fake_add
    db.flush = lambda: None
    db.commit = lambda: None
    db.refresh = lambda obj: None

    artifact = artifact_service.create_artifact(db, payload)

    assert artifact is created["artifact"]
    stored_path = tmp_path / artifact.storage_path
    assert stored_path.exists()
    assert stored_path.read_bytes() == b"hello"


def test_list_artifacts_empty():
    class _ScalarResult:
        def all(self):
            return []

    class _ExecuteResult:
        def scalars(self):
            return _ScalarResult()

    db = _Stub()
    db.execute = lambda query: _ExecuteResult()

    assert artifact_service.list_artifacts(db) == []


def test_decode_content_invalid():
    try:
        artifact_service.decode_content("not-base64")
    except ValueError as exc:
        assert "content_base64" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid base64")

from __future__ import annotations

from pathlib import Path


def test_no_non_py_schema_files():
    schemas_dir = Path(__file__).resolve().parents[1] / "schemas"
    bad = []
    for f in schemas_dir.iterdir():
        if f.is_file() and f.suffix != ".py" and f.name != "__pycache__":
            # allow __init__.py only; everything else must be .py
            bad.append(f.name)
    assert not bad, f"Unexpected non-.py files in app/schemas: {bad}"


def test_no_cyrillic_filenames_in_backend_app():
    app_dir = Path(__file__).resolve().parents[1]
    bad = []
    for f in app_dir.rglob("*"):
        if not f.is_file():
            continue
        name = f.name
        # crude cyrillic detection
        if any("\u0400" <= ch <= "\u04ff" for ch in name):
            bad.append(str(f.relative_to(app_dir)))
    assert not bad, f"Cyrillic filenames detected under backend/app: {bad}"

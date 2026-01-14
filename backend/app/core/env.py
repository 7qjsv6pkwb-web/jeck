from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# repo_root/.env (repo_root = .../jeck)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_PATH = _REPO_ROOT / ".env"

# Quietly load if present (no error if missing)
load_dotenv(_ENV_PATH, override=False)

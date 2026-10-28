"""Generează shared/schemas/*.schema.json din backend/app/models.py.
Rulează după orice schimbare de contract:  python scripts/export_schemas.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import AgentResult, Case, PipelineEvent  # noqa: E402

OUT = ROOT / "shared" / "schemas"
for name, model in {"case": Case, "agent_result": AgentResult, "event": PipelineEvent}.items():
    (OUT / f"{name}.schema.json").write_text(
        json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("scris", name)

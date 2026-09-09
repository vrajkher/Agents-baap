"""Compile successful observable work records into reusable skill packages."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class SkillCompiler:
    def __init__(self, skills_root: str | Path = "generated_skills") -> None:
        self.skills_root = Path(skills_root)
        self.skills_root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _slug(text: str) -> str:
        value = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")
        return value or "generated_skill"

    def compile(self, record: dict[str, Any], name: str | None = None) -> Path:
        if not record.get("skill_candidate"):
            raise ValueError("Record is not marked as a skill candidate.")

        skill_name = self._slug(name or record.get("goal", "generated_skill"))
        root = self.skills_root / skill_name
        root.mkdir(parents=True, exist_ok=True)

        workflow = {
            "name": skill_name,
            "goal": record.get("goal", ""),
            "source_run_id": record.get("run_id"),
            "inputs": sorted(record.get("inputs", {}).keys()),
            "output_requirements": record.get("output_requirements", []),
            "steps": [
                {
                    "kind": action.get("kind"),
                    "name": action.get("name"),
                    "status": action.get("status"),
                }
                for action in record.get("actions", [])
            ],
            "validation_checks": [v.get("check") for v in record.get("validations", [])],
            "replay_instruction": record.get("replay_instruction", ""),
        }

        (root / "workflow.json").write_text(
            json.dumps(workflow, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (root / "rules.json").write_text(
            json.dumps(record.get("rules", []), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (root / "reference_run.json").write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (root / "README.md").write_text(self._readme(skill_name, workflow), encoding="utf-8")
        return root

    @staticmethod
    def _readme(name: str, workflow: dict[str, Any]) -> str:
        steps = "\n".join(
            f"{i}. `{step['kind']}` → `{step['name']}`"
            for i, step in enumerate(workflow.get("steps", []), start=1)
        ) or "No steps recorded."
        return f"""# {name}\n\nGenerated from an approved observable AI working record.\n\n## Goal\n\n{workflow.get('goal', '')}\n\n## Replay instruction\n\n{workflow.get('replay_instruction', '')}\n\n## Recorded steps\n\n{steps}\n\n## Important\n\nThis package contains observable actions, rules, validations and outputs only. It does not contain private model chain-of-thought.\n"""

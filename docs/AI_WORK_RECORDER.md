# AI Work Recorder → Skill Compiler

The recorder turns successful, observable AI/agent work into reusable local skills.

It records only information available outside the model: goals, inputs, tool/actions, explicit decisions, business rules, validations, human corrections, artifacts, final results and replay instructions. It does **not** attempt to capture private chain-of-thought.

## Flow

```text
User goal
  -> AI/agent works
  -> WorkRecorder records observable execution
  -> human correction/approval
  -> successful run marked skill_candidate
  -> SkillCompiler freezes workflow + rules + reference run
  -> local agent can reuse the skill later
```

## Quick start

```bash
pip install -e .[dev]
python -m examples.work_recorder_demo
pytest tests/test_work_recorder.py
```

Default local database: `data/ai_work_records.db`.
Generated skills are written under `generated_skills/` unless another path is supplied.

## What to record from ChatGPT/OpenAI

- user goal and output requirements
- model/source name
- input files/data references
- observable tool/API calls made by your own application
- explicit decisions returned by the assistant
- deterministic business rules extracted and approved by a human
- validation checks and reconciliation results
- human corrections and approvals
- produced artifacts
- final result and reusable replay instruction

## Future adapters

Recommended next adapters:

1. OpenAI API response/tool-call adapter
2. Codex/Cursor CLI event adapter
3. Hermes Orchestrator hook that auto-starts and finishes records
4. Graphiti/Neo4j exporter for entity/relationship memory
5. ERPNext/Frappe skill runner
6. approval gate before a generated skill can execute production actions

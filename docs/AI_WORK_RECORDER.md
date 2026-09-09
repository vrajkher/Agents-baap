# AI Work Recorder → Graphiti Memory → Skill Compiler

The recorder turns successful, observable AI/agent work into reusable local skills and graph memory.

It records only externally observable information: goals, inputs, tool/actions, explicit decisions, business rules, validations, human corrections, artifacts, final results and replay instructions. It does **not** attempt to capture private chain-of-thought.

## Architecture

```text
User goal
  -> AI/agent works
  -> WorkRecorder records exact observable run in SQLite
  -> GraphitiWorkMemory stores the run as a structured episode
  -> Graphiti extracts entities + relationships + temporal facts
  -> Manager Agent searches prior experience/rules/relationships
  -> human correction/approval
  -> successful run marked skill_candidate
  -> SkillCompiler freezes workflow + rules + reference run
  -> local agent reuses the skill later
```

## Five memory layers

1. Knowledge memory — documents, facts, office details and reference material.
2. Graph memory — Graphiti relationships between offices, accounts, schemes, tasks, rules, decisions and outcomes.
3. Working memory — the active run currently being executed.
4. Experience memory — prior completed runs stored as Graphiti episodes plus the exact SQLite audit record.
5. Skill memory — frozen workflows/rules/scripts under `generated_skills/`.

## Why both SQLite and Graphiti?

SQLite is the deterministic audit log: it keeps the exact work record unchanged.
Graphiti is the reasoning/retrieval layer: it turns completed records into entities, relationships and searchable temporal experience.
Git/files are the executable skill layer: approved successful work can be frozen and replayed.

## Quick start without Graphiti

```bash
pip install -e .[dev]
python -m examples.work_recorder_demo
pytest tests/test_work_recorder.py
```

## Graphiti setup

Install the optional Graphiti dependency:

```bash
pip install -e .[graphiti]
```

Run a local Neo4j database, then set:

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=your-password
export OPENAI_API_KEY=your-key
```

Graphiti currently uses an LLM/embedding provider while ingesting/searching graph memory. Its default setup uses OpenAI unless another supported provider is configured.

Then run:

```bash
python -m examples.graphiti_work_memory_demo
```

The first Graphiti initialization calls `build_indices_and_constraints()`. Each completed AI run is then added through `add_episode(..., source=EpisodeType.json)`.

## What becomes a Graphiti episode?

Each completed record sends structured JSON containing:

- run ID and goal
- source/model
- context and inputs
- output requirements
- observable action log
- explicit AI decisions
- deterministic rules
- validations
- human corrections
- produced artifacts
- final result
- replay instruction
- skill-candidate flag and tags

This allows questions such as:

- What rule did we previously use for bank charges?
- Which FMR reconciliation runs were successful?
- What human correction changed this workflow?
- Which office/task used this rule before?
- What validation normally proves this process is complete?

## Freeze rule

Graph memory should learn from runs, but production execution should not depend on free-form memory alone. After one or more approved successful runs, freeze the stable process into:

```text
workflow + rules + scripts + validation + exception policy
```

The Manager Agent should prefer the frozen skill for repeat work and use Graphiti mainly to retrieve context, prior experience, relationships and exceptions.

## Next adapters

1. OpenAI API response/tool-call adapter
2. Codex/Cursor CLI event adapter
3. Hermes Orchestrator hook for automatic recording + Graphiti sync
4. ERPNext/Frappe skill runner
5. approval gate before generated skills execute production actions

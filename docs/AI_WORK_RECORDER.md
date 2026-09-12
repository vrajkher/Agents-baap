# AI Work Recorder → Graphiti Memory → Skill Compiler

The recorder turns successful, observable AI/agent work into reusable local skills and graph memory.

It records only externally observable information: goals, inputs, model outputs, tool/actions, explicit decisions, business rules, validations, human corrections, artifacts, final results and replay instructions. It does **not** attempt to capture private chain-of-thought.

## Architecture

```text
User goal
  -> ChatGPT/OpenAI Agent works
  -> OpenAI Agents SDK tracing emits trace + spans automatically
  -> Hermes OpenAITraceStore records every observable trace/span in SQLite
  -> compact completed trace is sent to Graphiti as an episode
  -> Graphiti extracts entities + relationships + temporal facts
  -> Manager Agent searches prior experience/rules/relationships
  -> human correction/approval
  -> successful stable method becomes a skill candidate
  -> SkillCompiler freezes workflow + rules + reference run
  -> local agent reuses the skill later
```

## Automatic ChatGPT/OpenAI work capture

Install the OpenAI Agents SDK integration:

```bash
pip install -e '.[openai]'
```

Or install both OpenAI capture and Graphiti:

```bash
pip install -e '.[full-memory]'
```

Then add one line before running your Agents SDK workflow:

```python
from hermes.recording import install_openai_agents_capture

install_openai_agents_capture("data/ai_work_records.db")
```

After that, every OpenAI Agents SDK trace handled by that Python process is copied into the local SQLite ledger automatically.

The capture processor records the observable trace/span stream exposed by the SDK, including where available:

- workflow/trace identity
- agent spans
- model generation spans
- function/tool calls and returned tool outputs
- handoffs between agents
- guardrail spans
- MCP/custom spans
- timestamps and parent/child relationships
- reported errors
- exported span payloads such as inputs/outputs when tracing includes them

The OpenAI Agents SDK has built-in tracing and sends trace/span lifecycle events to registered tracing processors. Hermes adds its recorder as an additional processor, so the local ledger can coexist with the SDK's normal tracing behavior.

### Important boundary

"Record all working" means **all observable working exposed by the application/SDK**. It does not mean private model chain-of-thought, hidden reasoning tokens, or other internal model state. Those are not exposed to the recorder.

Also remember that generation/function trace payloads can contain sensitive input/output data. Configure your application's privacy policy and OpenAI tracing settings appropriately before recording production/client information.

## Automatic trace → Graphiti

After a run completes:

```python
from hermes.recording import OpenAITraceStore, GraphitiWorkMemory

store = OpenAITraceStore("data/ai_work_records.db")
trace_id = store.latest_trace_id()
episode = store.to_graphiti_episode(trace_id)

memory = GraphitiWorkMemory()
await memory.initialize()
await memory.add_openai_trace(episode)
await memory.close()
```

The exact raw execution stays in SQLite. Graphiti receives the completed observable steps as an experience episode, so later agents can retrieve relationships such as which tool/rule/workflow produced a successful result.

A complete example is available at:

```bash
python -m examples.openai_auto_capture_demo
```

## Five memory layers

1. Knowledge memory — documents, facts, office details and reference material.
2. Graph memory — Graphiti relationships between offices, accounts, schemes, tasks, rules, decisions and outcomes.
3. Working memory — the active run currently being executed.
4. Experience memory — prior completed runs stored as Graphiti episodes plus the exact SQLite audit record.
5. Skill memory — frozen workflows/rules/scripts under `generated_skills/`.

## Why both SQLite and Graphiti?

SQLite is the deterministic audit log: it keeps the exact work/trace record unchanged.
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

Then run:

```bash
python -m examples.graphiti_work_memory_demo
```

## What becomes a Graphiti episode?

A manually structured work record can contain:

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

An automatic OpenAI trace episode can contain:

- trace/workflow ID
- ordered completed observable spans
- model/tool/agent/handoff/guardrail/custom span types
- parent-child execution relationships
- timing
- exported observable inputs/outputs
- errors and outcome metadata

This allows questions such as:

- What rule did we previously use for bank charges?
- Which FMR reconciliation runs were successful?
- What human correction changed this workflow?
- Which tools were used to complete this task?
- What sequence of observable steps worked last time?
- What validation normally proves this process is complete?

## Freeze rule

Graph memory should learn from runs, but production execution should not depend on free-form memory alone. After one or more approved successful runs, freeze the stable process into:

```text
workflow + rules + scripts + validation + exception policy
```

The Manager Agent should prefer the frozen skill for repeat work and use Graphiti mainly to retrieve context, prior experience, relationships and exceptions.

## Next adapters

1. Auto-classifier that converts completed traces into structured business rules/decisions/validations
2. Codex/Cursor CLI event adapter
3. Hermes Orchestrator hook for automatic Graphiti sync after each successful run
4. ERPNext/Frappe skill runner
5. approval gate before generated skills execute production actions

# Hermes Autonomous Agent OS

Hermes is a local-first Python framework for building, managing, and evolving
intelligent agents. It implements the eleven-component ecosystem described in
`docs/spec.xml`: a master Orchestrator, an agent builder, pluggable skills and
tools, short- and long-term memory, a message queue, an execution engine, an
error-handling layer, and a feedback-driven self-improvement loop — all with a
zero-dependency default runtime.

## Architecture

```
hermes/
├── core/            # Config, modes, privacy levels
├── orchestrator/    # Master "god" agent — plans, assigns, monitors
├── agents/          # Agent class + fluent AgentBuilder
├── skills/          # Reusable capability modules (filesystem, browser, ...)
├── tools/           # Low-level executors (python, shell, filesystem api)
├── memory/          # ShortTermMemory + LongTermMemory (JSON-backed)
├── communication/   # Typed message queue with event subscribers
├── execution/       # Run loop with retries and validation hooks
├── errors/          # Retry/fallback ErrorHandler with audit log
├── evolution/       # FeedbackLedger powers self-improvement scoring
└── security/        # Policy: path allowlist + destructive-command gate
```

## Quickstart

```bash
pip install -e .[dev]
python -m examples.hello_agent
python -m examples.accounting_flow
pytest
```

## Creating an agent

```python
from hermes import Orchestrator
from hermes.skills import default_skill_registry
from hermes.tools import default_tool_registry

orch = Orchestrator(skills=default_skill_registry(), tools=default_tool_registry())

def handler(agent, task):
    return {"echo": task["value"]}

agent = (
    orch.builder()
    .named("echo")
    .with_role("echo")
    .with_skills("FILE_SYSTEM_CONTROL")
    .with_tools("Python Executor")
    .with_handler(handler)
    .build()
)
orch.register_agent(agent)

print(orch.handle({"agent": "echo", "value": 42}))
```

## Built-in skills

| Skill | Functions |
| --- | --- |
| `FILE_SYSTEM_CONTROL` | `read_file`, `write_file`, `create_folder`, `delete_file` |
| `BROWSER_AUTOMATION` | `open_url`, `click`, `scrape`, `login`, `download` |
| `APPLICATION_CONTROL` | `open_app`, `interact_ui`, `send_input`, `read_output` |
| `ACCOUNTING_AUTOMATION` | `parse_invoice`, `generate_entry`, `validate_ledger`, `export_xml` |
| `API_INTEGRATION` | `GET`, `POST`, `AUTH`, `WEBHOOK` |

Browser and application skills ship as driver-agnostic stubs; wire them to
Playwright / pywinauto / pyautogui as needed by swapping the registered
functions on the skill instance.

## Security defaults

- File-system skills require an `allowed_roots` allowlist in `SecurityPolicy`.
- Shell commands matching destructive tokens (`rm -rf`, `mkfs`, …) require an
  explicit `confirmed=True`.
- Secrets are assumed encrypted at rest — the framework never writes raw tokens
  to the long-term JSON store unless you put them there.

## Self-evolution

Every orchestrator run records an entry in `FeedbackLedger`. Use
`orchestrator.feedback.score(agent_name)` or `best_performing()` to surface
agents for reinforcement, retirement, or rebuilding with additional skills.

"""Demo: automatically capture an OpenAI Agents SDK run and sync it to Graphiti.

Prerequisites:
    pip install -e '.[full-memory]'
    export OPENAI_API_KEY=...
    export NEO4J_URI=bolt://localhost:7687
    export NEO4J_USER=neo4j
    export NEO4J_PASSWORD=...
"""

from __future__ import annotations

import asyncio

from agents import Agent, Runner

from hermes.recording import (
    GraphitiWorkMemory,
    OpenAITraceStore,
    install_openai_agents_capture,
)

DB_PATH = "data/ai_work_records.db"

# One line installs automatic local recording for all subsequent Agents SDK traces.
install_openai_agents_capture(DB_PATH)

agent = Agent(
    name="Demo Work Agent",
    instructions="Answer clearly and use tools when available.",
)


async def main() -> None:
    result = await Runner.run(agent, "Explain what an FMR reconciliation should produce.")
    print(result.final_output)

    # The trace and every observable span are already in SQLite at this point.
    store = OpenAITraceStore(DB_PATH)
    trace_id = store.latest_trace_id()
    if not trace_id:
        raise RuntimeError("No local OpenAI trace was captured.")

    # Convert the exact trace into a compact graph episode and store it in Graphiti.
    episode = store.to_graphiti_episode(trace_id)
    memory = GraphitiWorkMemory()
    await memory.initialize()
    await memory.add_openai_trace(episode)
    await memory.close()

    print(f"Captured trace: {trace_id}")
    print("Synced observable work trace to Graphiti.")


if __name__ == "__main__":
    asyncio.run(main())

"""Smallest possible Hermes demo.

Run with::

    python -m examples.hello_agent
"""
from hermes import Orchestrator
from hermes.skills import default_skill_registry
from hermes.tools import default_tool_registry


def greet_handler(agent, task):
    who = task.get("name", "world")
    message = f"Hello, {who}! -- from {agent.spec.name}"
    print(message)
    return {"message": message}


def main() -> None:
    orch = Orchestrator(skills=default_skill_registry(), tools=default_tool_registry())

    greeter = (
        orch.builder()
        .named("greeter")
        .with_role("greeter")
        .with_skills("FILE_SYSTEM_CONTROL")
        .with_tools("Python Executor")
        .with_handler(greet_handler)
        .build()
    )
    orch.register_agent(greeter)

    results = orch.handle({"agent": "greeter", "name": "Hermes"})
    print("results:", results)
    print("agent score:", orch.feedback.score("greeter"))


if __name__ == "__main__":
    main()

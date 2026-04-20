"""Hermes Autonomous Agent OS.

Top-level package that exposes the orchestrator, agent builder, and registries.
"""

from hermes.core.config import HermesConfig
from hermes.orchestrator.orchestrator import Orchestrator
from hermes.agents.builder import AgentBuilder
from hermes.agents.base import Agent, AgentSpec

__all__ = [
    "HermesConfig",
    "Orchestrator",
    "AgentBuilder",
    "Agent",
    "AgentSpec",
]

__version__ = "0.1.0"

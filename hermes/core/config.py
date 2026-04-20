from dataclasses import dataclass, field
from pathlib import Path

from hermes.core.constants import ExecutionMode, NetworkMode, PrivacyLevel


@dataclass
class HermesConfig:
    system_name: str = "Hermes Autonomous Agent OS"
    mission: str = (
        "Build, manage, and evolve intelligent agents that can autonomously "
        "perform tasks, create new agents, and integrate with local and external systems."
    )
    execution_mode: ExecutionMode = ExecutionMode.LOCAL_FIRST
    network_mode: NetworkMode = NetworkMode.OPTIONAL
    privacy: PrivacyLevel = PrivacyLevel.STRICT

    state_dir: Path = field(default_factory=lambda: Path(".hermes_state"))
    max_retries: int = 3

    def ensure_state_dir(self) -> Path:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        return self.state_dir

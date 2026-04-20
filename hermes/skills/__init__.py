from hermes.skills.base import Skill, SkillRegistry
from hermes.skills.filesystem import FileSystemControl
from hermes.skills.browser import BrowserAutomation
from hermes.skills.application import ApplicationControl
from hermes.skills.accounting import AccountingAutomation
from hermes.skills.api_integration import APIIntegration

__all__ = [
    "Skill",
    "SkillRegistry",
    "FileSystemControl",
    "BrowserAutomation",
    "ApplicationControl",
    "AccountingAutomation",
    "APIIntegration",
]


def default_skill_registry() -> dict[str, Skill]:
    return {
        s.name: s
        for s in (
            FileSystemControl(),
            BrowserAutomation(),
            ApplicationControl(),
            AccountingAutomation(),
            APIIntegration(),
        )
    }

from __future__ import annotations

from hermes.skills.base import Skill


class BrowserAutomation(Skill):
    """Placeholder for a browser-automation backend (e.g. Playwright, Selenium).

    Each function returns a descriptor so callers can record intent even when no
    browser driver is installed. Wire a real driver by replacing the registered
    functions with concrete implementations.
    """

    name = "BROWSER_AUTOMATION"

    def _install_functions(self) -> None:
        self.register("open_url", self.open_url)
        self.register("click", self.click)
        self.register("scrape", self.scrape)
        self.register("login", self.login)
        self.register("download", self.download)

    def open_url(self, url: str) -> dict[str, str]:
        return {"action": "open_url", "url": url, "status": "pending-driver"}

    def click(self, selector: str) -> dict[str, str]:
        return {"action": "click", "selector": selector, "status": "pending-driver"}

    def scrape(self, selector: str, attribute: str | None = None) -> dict[str, str]:
        return {
            "action": "scrape",
            "selector": selector,
            "attribute": attribute or "text",
            "status": "pending-driver",
        }

    def login(self, url: str, username: str, password: str) -> dict[str, str]:
        return {
            "action": "login",
            "url": url,
            "username": username,
            "status": "pending-driver",
        }

    def download(self, url: str, destination: str) -> dict[str, str]:
        return {
            "action": "download",
            "url": url,
            "destination": destination,
            "status": "pending-driver",
        }

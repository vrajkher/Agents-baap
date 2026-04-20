"""Multi-agent accounting demo: parse invoice -> post entry -> export XML.

Run with::

    python -m examples.accounting_flow
"""
from hermes import Orchestrator
from hermes.skills import default_skill_registry
from hermes.skills.accounting import Invoice
from hermes.tools import default_tool_registry


INVOICE_TEXT = """
INVOICE: INV-2026-0001
VENDOR: Acme Stationery
DATE: 2026-04-15
LINE: A4 paper ream | 250.00 | 4
LINE: Stapler | 120.00 | 2
"""


def parse_handler(agent, task):
    skill = agent.skill_registry["ACCOUNTING_AUTOMATION"]
    invoice = skill.invoke("parse_invoice", task["text"])
    return {"invoice": invoice}


def post_handler(agent, task):
    skill = agent.skill_registry["ACCOUNTING_AUTOMATION"]
    invoice: Invoice = task["invoice"]
    entry = skill.invoke("generate_entry", invoice, expense_account="Office Supplies")
    valid = skill.invoke("validate_ledger", [entry])
    xml = skill.invoke("export_xml", entry)
    return {"entry": entry, "valid": valid, "xml": xml}


def main() -> None:
    orch = Orchestrator(skills=default_skill_registry(), tools=default_tool_registry())

    parser = (
        orch.builder()
        .named("invoice-parser")
        .with_role("invoice-parser")
        .with_skills("ACCOUNTING_AUTOMATION")
        .with_handler(parse_handler)
        .build()
    )
    poster = (
        orch.builder()
        .named("ledger-poster")
        .with_role("ledger-poster")
        .with_skills("ACCOUNTING_AUTOMATION")
        .with_handler(post_handler)
        .build()
    )
    orch.register_agent(parser)
    orch.register_agent(poster)

    parsed = orch.handle({"agent": "invoice-parser", "text": INVOICE_TEXT})
    invoice = parsed[0]["outcome"].output["invoice"]

    posted = orch.handle({"agent": "ledger-poster", "invoice": invoice})
    print("posted entry:", posted[0]["outcome"].output["entry"])
    print("ledger valid:", posted[0]["outcome"].output["valid"])
    print("xml:\n" + posted[0]["outcome"].output["xml"])


if __name__ == "__main__":
    main()

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

from hermes.skills.base import Skill


@dataclass
class InvoiceLine:
    description: str
    amount: float
    quantity: float = 1.0


@dataclass
class Invoice:
    invoice_id: str
    vendor: str
    date: str
    lines: list[InvoiceLine]

    @property
    def total(self) -> float:
        return sum(line.amount * line.quantity for line in self.lines)


class AccountingAutomation(Skill):
    """Accounting helpers tailored for SMB workflows (Tally-style)."""

    name = "ACCOUNTING_AUTOMATION"

    def _install_functions(self) -> None:
        self.register("parse_invoice", self.parse_invoice)
        self.register("generate_entry", self.generate_entry)
        self.register("validate_ledger", self.validate_ledger)
        self.register("export_xml", self.export_xml)

    def parse_invoice(self, text: str) -> Invoice:
        """Naive invoice parser for unit tests and examples.

        Expected lines, one per field::

            INVOICE: INV-001
            VENDOR: Acme Corp
            DATE: 2026-01-15
            LINE: Description | amount | quantity
        """
        invoice_id = vendor = date = ""
        lines: list[InvoiceLine] = []
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip().upper(), value.strip()
            if key == "INVOICE":
                invoice_id = value
            elif key == "VENDOR":
                vendor = value
            elif key == "DATE":
                date = value
            elif key == "LINE":
                parts = [p.strip() for p in value.split("|")]
                description = parts[0] if parts else ""
                amount = float(parts[1]) if len(parts) > 1 else 0.0
                quantity = float(parts[2]) if len(parts) > 2 else 1.0
                lines.append(InvoiceLine(description, amount, quantity))
        if not invoice_id:
            raise ValueError("Invoice missing INVOICE id")
        return Invoice(invoice_id=invoice_id, vendor=vendor, date=date, lines=lines)

    def generate_entry(self, invoice: Invoice, expense_account: str = "Expenses") -> dict[str, Any]:
        return {
            "invoice_id": invoice.invoice_id,
            "date": invoice.date,
            "debit": [{"account": expense_account, "amount": invoice.total}],
            "credit": [{"account": f"Creditors/{invoice.vendor}", "amount": invoice.total}],
        }

    def validate_ledger(self, entries: list[dict[str, Any]]) -> bool:
        for entry in entries:
            debit = sum(row["amount"] for row in entry.get("debit", []))
            credit = sum(row["amount"] for row in entry.get("credit", []))
            if not self._almost_equal(debit, credit):
                return False
        return True

    def export_xml(self, entry: dict[str, Any]) -> str:
        root = Element("VOUCHER", attrib={"INVOICE": entry.get("invoice_id", "")})
        SubElement(root, "DATE").text = entry.get("date", "")
        for side in ("debit", "credit"):
            container = SubElement(root, side.upper())
            for row in entry.get(side, []):
                item = SubElement(container, "LEDGER")
                item.set("account", str(row.get("account", "")))
                item.text = f"{float(row.get('amount', 0)):.2f}"
        return tostring(root, encoding="unicode")

    @staticmethod
    def _almost_equal(a: float, b: float, tolerance: float = 0.01) -> bool:
        return abs(a - b) <= tolerance

    @staticmethod
    def _sanitize(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

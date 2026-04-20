from pathlib import Path

import pytest

from hermes.security.policy import SecurityPolicy, SecurityViolation
from hermes.skills.accounting import AccountingAutomation
from hermes.skills.filesystem import FileSystemControl


def test_filesystem_policy_blocks_out_of_scope(tmp_path: Path) -> None:
    policy = SecurityPolicy(allowed_roots=[tmp_path])
    fs = FileSystemControl(policy=policy)

    fs.write_file(tmp_path / "a.txt", "hello")
    assert fs.read_file(tmp_path / "a.txt") == "hello"

    outside = tmp_path.parent / "not-allowed.txt"
    with pytest.raises(SecurityViolation):
        fs.write_file(outside, "nope")


def test_filesystem_delete_requires_confirmation(tmp_path: Path) -> None:
    fs = FileSystemControl(policy=SecurityPolicy(allowed_roots=[tmp_path]))
    target = tmp_path / "doomed.txt"
    fs.write_file(target, "data")

    with pytest.raises(PermissionError):
        fs.delete_file(target)
    assert fs.delete_file(target, confirmed=True) is True
    assert not target.exists()


def test_accounting_parse_and_entry_roundtrip() -> None:
    skill = AccountingAutomation()
    invoice = skill.invoke(
        "parse_invoice",
        """
        INVOICE: INV-1
        VENDOR: Foo Ltd
        DATE: 2026-01-01
        LINE: Widgets | 100.00 | 2
        """,
    )
    entry = skill.invoke("generate_entry", invoice)
    assert invoice.total == 200.0
    assert entry["debit"][0]["amount"] == 200.0
    assert skill.invoke("validate_ledger", [entry]) is True
    xml = skill.invoke("export_xml", entry)
    assert "INV-1" in xml and "200.00" in xml

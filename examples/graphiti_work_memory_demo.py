"""Demo: push a completed Hermes work record into Graphiti and search it."""

import asyncio

from hermes.recording import GraphitiWorkMemory, WorkRecorder


async def main() -> None:
    recorder = WorkRecorder("data/graphiti_demo_records.db")
    recorder.start(
        "Prepare FMR reconciliation for Bagodara",
        model="gpt-5.6-sol",
        source="chatgpt",
        inputs={"office": "Bagodara", "bank_statement": "bank.xlsx", "audited_fmr": "fmr.xlsx"},
        output_requirements=["final reconciliation report", "exception list"],
        tags=["accounting", "fmr", "reconciliation"],
    )
    recorder.action("file", "read_audited_fmr", input={"path": "fmr.xlsx"})
    recorder.action("file", "read_bank_statement", input={"path": "bank.xlsx"})
    recorder.rule(
        "bank_charge_adjustment",
        condition="transaction_type == bank_charge",
        action="add_to_reconciliation_adjustment",
    )
    recorder.decision(
        "Classify the unmatched debit as a bank charge after evidence review",
        basis="bank narration and supporting evidence",
        confidence=0.96,
    )
    recorder.validate("closing balance reconciles", True, "difference = 0")
    recorder.correction("Human approved the bank-charge classification")
    finished = recorder.finish(
        {"status": "success", "office": "Bagodara", "exceptions": 0},
        replay_instruction="Use the same workflow for another office with new FMR and bank files.",
        skill_candidate=True,
    )

    memory = GraphitiWorkMemory()
    try:
        await memory.initialize()
        await memory.add_work_record(finished.to_dict())

        results = await memory.search("How should bank charges be handled in FMR reconciliation?")
        for result in results:
            print(result["fact"])
    finally:
        await memory.close()


if __name__ == "__main__":
    asyncio.run(main())

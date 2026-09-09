"""Demo: record one successful AI task and compile it into a reusable skill."""

from hermes.recording import SkillCompiler, WorkRecorder


recorder = WorkRecorder("data/demo_work_records.db")
record = recorder.start(
    "Prepare FMR reconciliation",
    model="gpt-5.6-sol",
    source="chatgpt",
    inputs={"bank_statement": "bank.xlsx", "audited_fmr": "fmr.xlsx"},
    output_requirements=["final reconciliation report", "exception list"],
    tags=["accounting", "reconciliation"],
)

recorder.action("file", "read_audited_fmr", input={"path": "fmr.xlsx"})
recorder.action("file", "read_bank_statement", input={"path": "bank.xlsx"})
recorder.rule(
    "bank_charge_adjustment",
    condition="transaction_type == bank_charge",
    action="add_to_reconciliation_adjustment",
)
recorder.decision(
    "Treat unmatched debit as bank charge after supporting evidence was found",
    basis="bank narration and supporting document",
    confidence=0.96,
)
recorder.validate("closing balance reconciles", True, "difference = 0")
recorder.correction("Human approved bank-charge classification")
recorder.artifact("outputs/Bagodara_Reconciliation.xlsx")

finished = recorder.finish(
    {"status": "success", "exceptions": 0},
    replay_instruction="Use the same workflow for a new office with new FMR and bank files.",
    skill_candidate=True,
)

compiler = SkillCompiler("generated_skills")
skill_path = compiler.compile(finished.to_dict(), name="fmr_reconciliation")
print(f"Saved run: {finished.run_id}")
print(f"Generated skill: {skill_path}")

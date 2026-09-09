from pathlib import Path

from hermes.recording import ChatGPTDesktopRecorder


recorder = ChatGPTDesktopRecorder()

session_id = recorder.start_session(
    "Prepare FMR reconciliation using ChatGPT Desktop"
)

recorder.record_prompt(
    "Read the audited FMR and bank statement, reconcile them, and create a reusable Python script."
)

recorder.record_response(
    "Visible ChatGPT Desktop answer can be pasted here or passed by a companion UI."
)

recorder.record_script(
    "def reconcile(fmr_total, bank_total):\n    return bank_total - fmr_total\n",
    language="python",
    filename="reconcile.py",
)

# Optional: capture scripts/files ChatGPT created in a user-selected work folder.
work_folder = Path("desktop_work")
if work_folder.exists():
    artifacts = recorder.snapshot_working_files(work_folder)
    print(f"Captured {len(artifacts)} file artifacts")

recorder.record_validation("reconciliation_difference_zero", True, "difference = 0")
recorder.record_correction("Human approved the final bank-charge rule")

record = recorder.finish_session(
    "FMR reconciliation completed and reusable script approved",
    approved=True,
)

print(f"Desktop session recorded: {session_id}")
print(f"Events: {len(record['events'])}")
print(f"Artifacts: {len(record['artifacts'])}")
recorder.close()

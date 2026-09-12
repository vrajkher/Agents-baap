# ChatGPT Desktop Work Recorder

This companion records **observable** work done with ChatGPT Desktop and sends it into the same local AI Working Record architecture used by Hermes.

It does **not** read ChatGPT private internals, hidden chain-of-thought, or hidden reasoning tokens.

## What it records

- your visible prompt
- ChatGPT's visible response
- generated scripts/code you pass to the companion
- files in a folder you explicitly select
- file snapshots with SHA-256 hashes
- corrections you make
- validation results
- final approved result

## Local data flow

```text
ChatGPT Desktop
   -> visible prompt/answer
   -> ChatGPTDesktopRecorder
   -> SQLite exact audit log
   -> artifact snapshots
   -> Graphiti experience memory (next sync step)
   -> approved successful work
   -> reusable skill
```

## Install

```bash
git checkout feature/ai-work-recorder
pip install -e .
```

## Run the demo

```bash
python -m examples.chatgpt_desktop_recorder_demo
```

By default it creates:

```text
data/chatgpt_desktop_work.db
data/chatgpt_desktop_artifacts/
```

## Basic Python use

```python
from hermes.recording import ChatGPTDesktopRecorder

r = ChatGPTDesktopRecorder()
r.start_session("Reconcile Bagodara FMR")
r.record_prompt("Reconcile this FMR and bank statement")
r.record_response("Paste/pass the visible ChatGPT answer here")
r.record_script("print('example')", filename="reconcile.py")
r.snapshot_working_files("desktop_work")
r.record_validation("difference zero", True, "difference = 0")
r.record_correction("Use bank-charge adjustment rule")
r.finish_session("Completed", approved=True)
r.close()
```

## Privacy design

The recorder intentionally does not install a system-wide keylogger or silent clipboard logger. Text must be explicitly passed to the recorder and folders must be explicitly selected. This reduces accidental capture of passwords, API keys, private messages, and unrelated applications.

## Recommended next desktop layer

A small local tray/companion app can add:

1. Start Recording button
2. Capture Current Prompt/Answer button
3. Select Working Folder
4. Auto-detect changed scripts/files inside that selected folder
5. Mark Correction
6. Validate Result
7. Approve & Freeze Skill
8. Sync completed record to Graphiti

The companion should still record only observable user-selected material, not private ChatGPT reasoning.

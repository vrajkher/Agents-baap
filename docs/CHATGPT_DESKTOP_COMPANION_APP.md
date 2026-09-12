# ChatGPT Desktop Work Recorder — Windows Companion App

A simple local Windows GUI for recording observable ChatGPT Desktop work into a reusable work history and skill library.

## What it records

- User-entered goal
- Prompt/instruction text that the user explicitly pastes/types into the companion
- ChatGPT visible answer/code/script that the user explicitly pastes/types into the companion
- Created, modified and deleted files inside the user-selected work folder
- Snapshots of created/modified files
- Human corrections
- Validation text
- Final result
- Approval status
- Frozen skill reference run

## What it does NOT record

- Hidden/private model chain-of-thought
- System-wide keystrokes
- Global clipboard contents
- Other folders unless the user selects them
- Private ChatGPT internal execution that is not exposed to the user

## Start on Windows

From the repository root:

```bat
run_chatgpt_desktop_recorder.bat
```

Or:

```bash
python apps/chatgpt_desktop_companion.py
```

Tkinter is included with standard Windows Python installations in most cases.

## Typical workflow

1. Enter the Goal.
2. Select the folder where ChatGPT is creating/editing files.
3. Click **Start Recording**.
4. Paste the prompt and visible ChatGPT response/code, then click **Capture Prompt + Answer**.
5. After ChatGPT creates/changes files, click **Scan Changed Files**.
6. Use **Record Correction** whenever you correct ChatGPT.
7. Enter a validation such as `difference = 0` or `report reviewed`.
8. Click **Approve** for a successful run.
9. Click **Freeze as Skill** to create a reusable skill record under `generated_skills/`.

## Local outputs

```text
data/chatgpt_desktop_companion.db
data/chatgpt_desktop_artifacts/<run_id>/
generated_skills/<skill_name>/
```

## Current boundary

The ChatGPT Desktop application does not provide this project with a direct official event stream for every visible message and internal action. Therefore, chat text is captured through explicit user paste/type into the companion. File changes inside a selected folder can be detected and snapshotted locally.

A future adapter can add supported desktop/app integrations if an official event/API surface becomes available.

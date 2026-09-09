from pathlib import Path

from hermes.recording import SkillCompiler, WorkRecorder


def test_record_and_compile(tmp_path: Path) -> None:
    db = tmp_path / "records.db"
    recorder = WorkRecorder(db)
    active = recorder.start(
        "Test reusable task",
        model="test-model",
        inputs={"input_file": "sample.txt"},
        output_requirements=["result"],
    )
    recorder.action("tool", "read_file", input={"path": "sample.txt"})
    recorder.rule("example", "input_exists", "process_input")
    recorder.validate("result exists", True)
    finished = recorder.finish(
        {"result": "ok"},
        replay_instruction="Repeat with a new input file.",
        skill_candidate=True,
    )

    loaded = recorder.get(active.run_id)
    assert loaded is not None
    assert loaded["goal"] == "Test reusable task"
    assert loaded["skill_candidate"] is True

    compiler = SkillCompiler(tmp_path / "skills")
    path = compiler.compile(finished.to_dict(), name="test_skill")
    assert (path / "workflow.json").exists()
    assert (path / "rules.json").exists()
    assert (path / "reference_run.json").exists()

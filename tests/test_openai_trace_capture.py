from pathlib import Path

from hermes.recording import OpenAITraceStore


class FakeTrace:
    trace_id = "trace_test123"
    name = "Test Workflow"
    started_at = "2026-09-09T10:00:00+00:00"
    ended_at = "2026-09-09T10:00:05+00:00"

    def export(self):
        return {"trace_id": self.trace_id, "workflow_name": self.name}


class FakeSpanData:
    type = "function"

    def export(self):
        return {
            "type": "function",
            "name": "read_file",
            "input": '{"path":"fmr.xlsx"}',
            "output": "rows=10",
        }


class FakeSpan:
    trace_id = "trace_test123"
    span_id = "span_1"
    parent_id = None
    started_at = "2026-09-09T10:00:01+00:00"
    ended_at = "2026-09-09T10:00:02+00:00"
    error = None
    span_data = FakeSpanData()


def test_openai_trace_store_and_graphiti_episode(tmp_path: Path) -> None:
    store = OpenAITraceStore(tmp_path / "records.db")
    trace = FakeTrace()
    span = FakeSpan()

    store.trace_start(trace)
    store.span_event("span_start", span)
    store.span_event("span_end", span)
    store.trace_end(trace)

    loaded = store.get_trace(trace.trace_id)
    assert loaded is not None
    assert loaded["trace"]["workflow_name"] == "Test Workflow"
    assert len(loaded["events"]) == 2

    episode = store.to_graphiti_episode(trace.trace_id)
    assert episode["memory_type"] == "openai_agent_work_trace"
    assert episode["trace_id"] == trace.trace_id
    assert len(episode["observable_steps"]) == 1
    assert episode["observable_steps"][0]["span_type"] == "function"
    assert episode["observable_steps"][0]["payload"]["name"] == "read_file"

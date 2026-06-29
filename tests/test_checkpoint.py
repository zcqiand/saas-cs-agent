import os
from saas_cs_agent.checkpoint import make_checkpointer
from saas_cs_agent.state import CSState
from saas_cs_agent.llm import FakeLLM


def test_state_defaults():
    s: CSState = {"messages": [], "thread_id": "t1", "tenant_id": "acme", "intent": "", "awaiting_human": False}
    assert s["thread_id"] == "t1"


def test_fake_llm_returns_scripted():
    llm = FakeLLM(script=["hello", "world"])
    assert llm.generate("x") == "hello"
    assert llm.generate("y") == "world"


def test_make_checkpointer_returns_sqlite_saver(tmp_path):
    db = str(tmp_path / "cp.db")
    saver = make_checkpointer(db)
    assert saver is not None
    # it should be a BaseCheckpointSaver
    from langgraph.checkpoint.base import BaseCheckpointSaver
    assert isinstance(saver, BaseCheckpointSaver)


def test_make_checkpointer_postgres_without_pkg_raises(tmp_path):
    # if langgraph-checkpoint-postgres not installed, expect ImportError (skip if installed)
    try:
        import langgraph.checkpoint.postgres  # noqa
        return  # installed → nothing to assert
    except ImportError:
        import pytest
        with pytest.raises(ImportError):
            make_checkpointer("postgresql://localhost/db")

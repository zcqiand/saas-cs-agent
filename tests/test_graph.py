from saas_cs_agent.checkpoint import make_checkpointer
from saas_cs_agent.graph import build_graph
from saas_cs_agent.llm import FakeLLM


def _initial():
    return {"messages": [{"role": "user", "content": "密码忘了"}],
            "thread_id": "acme:s1", "tenant_id": "acme", "intent": "", "awaiting_human": False}


def test_graph_interrupts_before_human_review(tmp_path):
    saver = make_checkpointer(str(tmp_path / "cp.db"))
    llm = FakeLLM(script=["password_reset", "请访问 /reset 重置密码"])
    g = build_graph(checkpointer=saver, llm=llm)
    config = {"configurable": {"thread_id": "acme:s1"}}
    g.invoke(_initial(), config)
    state = g.get_state(config)
    assert state.next  # paused, not at END
    assert "human_review" in state.next


def test_graph_resumes_to_end(tmp_path):
    saver = make_checkpointer(str(tmp_path / "cp.db"))
    llm = FakeLLM(script=["password_reset", "请访问 /reset 重置密码"])
    g = build_graph(checkpointer=saver, llm=llm)
    config = {"configurable": {"thread_id": "acme:s1"}}
    g.invoke(_initial(), config)
    g.invoke(None, config)  # resume past human_review
    final = g.get_state(config)
    assert not final.next  # reached END
    assert final.values["awaiting_human"] is False

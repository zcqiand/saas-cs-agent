from saas_cs_agent.checkpoint import make_checkpointer
from saas_cs_agent.graph import build_graph
from saas_cs_agent.llm import FakeLLM
from saas_cs_agent.time_travel import list_history, fork_from


def _initial(msg="密码忘了"):
    return {"messages": [{"role": "user", "content": msg}],
            "thread_id": "acme:s1", "tenant_id": "acme", "intent": "", "awaiting_human": False}


def _graph(tmp_path):
    saver = make_checkpointer(str(tmp_path / "cp.db"))
    llm = FakeLLM(script=["password_reset", "reply1"])
    return build_graph(checkpointer=saver, llm=llm)


def test_list_history_returns_snapshots(tmp_path):
    g = _graph(tmp_path)
    cfg = {"configurable": {"thread_id": "acme:s1"}}
    g.invoke(_initial("问题A"), cfg)
    hist = list_history(g, "acme:s1")
    assert len(hist) >= 2  # multiple checkpoints recorded


def test_fork_from_creates_divergent_thread(tmp_path):
    g = _graph(tmp_path)
    cfg = {"configurable": {"thread_id": "acme:s1"}}
    g.invoke(_initial("问题A"), cfg)
    hist = list_history(g, "acme:s1")
    early_id = hist[-1].config["configurable"]["checkpoint_id"]
    # fork from early checkpoint with a different user message
    fork_input = {"messages": [{"role": "user", "content": "问题B"}],
                  "thread_id": "acme:fork", "tenant_id": "acme", "intent": "", "awaiting_human": False}
    fork_from(g, early_id, fork_input, "acme:fork")
    fork_state = g.get_state({"configurable": {"thread_id": "acme:fork"}})
    assert fork_state.values is not None
    assert fork_state.values["messages"][0]["content"] == "问题B"

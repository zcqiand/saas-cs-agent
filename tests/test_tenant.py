from saas_cs_agent.tenant import thread_id_for, TenantRouter


def test_thread_id_isolated_by_tenant():
    assert thread_id_for("acme", "s1") == "acme:s1"
    assert thread_id_for("acme", "s1") != thread_id_for("globex", "s1")


def test_thread_id_isolated_by_session():
    assert thread_id_for("acme", "s1") != thread_id_for("acme", "s2")


def test_router_register_and_get():
    r = TenantRouter()
    tid = r.register("acme", "s1")
    assert r.get_thread("acme", "s1") == tid == "acme:s1"

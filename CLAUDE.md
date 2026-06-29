# saas-cs-agent — 项目级上下文

多租户持久化客服 Agent + 时间旅行（基于 LangGraph checkpointer）。

- 技术栈：Python 3.10+ / LangGraph 1.2.x / SQLite（默认，checkpointer 持久化）
- 测试用 `FakeLLM`，无需任何 API Key、无需联网
- 运行：`pytest -q`（无 API Key）

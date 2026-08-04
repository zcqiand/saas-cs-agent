# 多租户持久化客服

多租户持久化客服 + 时间旅行（LangGraph checkpointer）。配套《Codex 从入门到项目实践》卷四。

## 快速开始

```bash
pip install -e ".[dev]"    # 安装依赖
pytest -q                   # 跑全部测试（FakeLLM，无需 API Key）
```

## 功能特性

- **持久化检查点**：LangGraph checkpointer，线程级状态恢复
- **多租户隔离与并发**：租户数据完全隔离，支持并发会话
- **时间旅行回溯**：历史状态查询与回滚

## 技术栈

| 技术 | 版本 |
| :--- | :--- |
| Python | 3.10+ |
| LangGraph | 1.2.x |
| SQLite（checkpointer 默认） | — |
| 测试框架 | pytest 8.x |

> 依赖版本与 `version-lock.json` 的 `version_lock` 一致，不引入 lock 外的库。

## 配套书籍及章节映射

| 章 | 主题 | 对应源文件 |
| :--- | :--- | :--- |
| 26 | 持久化检查点 | `checkpoint.py`, `graph.py` |
| 27 | 多租户隔离与并发 | `tenant.py`, `state.py` |
| 28 | 时间旅行回溯 | `time_travel.py` |

## 快速链接

- [功能规格文档.md](功能规格文档.md) — 功能名称、描述与验收标准
- [CLAUDE.md](CLAUDE.md) — 开发约定与编码规范

# saas-cs-agent — 仓库工作约定（供 Claude Code）

本仓为《Codex 从入门到项目实践》卷四案例仓（多租户持久化客服）的可运行配套工程，是书稿代码块的 **source of truth**。

## 项目定位

多租户持久化客服 Agent + 时间旅行（基于 LangGraph checkpointer），用于演示线程级状态持久化、多租户隔离与历史状态回溯。

## 铁律

- **TDD**：每个模块先写失败测试 → 跑确认失败 → 实现 → 跑确认绿 → commit。
- **版本钉死**：依赖与 `version-lock.json` 的 `version_lock` 一致；不引入 lock 外的库。
- **tag 即放行**：全量回归绿后打 `v<MAJOR>.<MINOR>-<NNN>`（NNN=项目号）。
- **只增不改**：扩充时不动现有模块签名/行为；新模块独立测试，CI 双跑。
- **mock-friendly**：`pip install -e ".[dev]" && pytest -q` 必须在无 Key、无 Docker、无网下全绿。

## 技术栈与版本（钉死于 version-lock.json）

- Python 3.10+
- LangGraph 1.2.x
- SQLite（checkpointer 默认持久化）
- pytest 8.x

## 验收

```bash
pip install -e ".[dev]"    # 离线可用（首次需联网，之后 node_modules 已就绪）
pytest -q                   # 必须全绿，无需 Key/Docker/网络
```

## 目录结构

```text
saas-cs-agent/
├── pyproject.toml
├── CLAUDE.md
├── version-lock.json
├── src/
│   ├── checkpoint.py              ← Ch26 持久化检查点
│   ├── graph.py
│   ├── tenant.py                  ← Ch27 多租户隔离
│   ├── state.py
│   └── time_travel.py             ← Ch28 时间旅行回溯
└── tests/
```

## 编码约定

- **FakeLLM 驱动**：所有测试用 `FakeLLM`，无需任何 API Key、无需联网。
- **租户隔离**：跨租户状态不可访问，测试需覆盖隔离场景。
- **零伪代码**：禁止 `pass` 占位、`TODO` 占位，每段代码必须可运行。

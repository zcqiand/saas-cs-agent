# Task 3.1 — foundation（仓骨架 + state + checkpointer + FakeLLM）

仓库：`code/saas-cs-agent`（独立 git repo，已 `git init`，未 push）
分支：`main`
Commit：`0f4f6634809d5d77673a1e52ca0190e395361c8f`
方法：严格 TDD（先写失败测试 → 确认 FAIL → 实现 → PASS → commit）

## 交付文件（11 个，全部已提交）

```
code/saas-cs-agent/
├── .gitignore                      # __pycache__/ *.pyc .pytest_cache/ *.db
├── .env.example                    # # 无需 API Key（FakeLLM 跑测试）
├── CLAUDE.md                       # 项目级上下文
├── README.md                       # 名称 + 一句话定位 + 卷四案例仓归属
├── pyproject.toml                  # name/version/3.10+/deps/pytest pythonpath
├── src/saas_cs_agent/
│   ├── __init__.py                 # 空
│   ├── state.py                    # CSState TypedDict
│   ├── llm.py                      # FakeLLM
│   └── checkpoint.py               # make_checkpointer 工厂 + close_all
└── tests/
    ├── __init__.py                 # 空
    └── test_checkpoint.py          # 4 个测试
```

## 模块要点

### `state.py` — `CSState(TypedDict)`
字段：`messages: list`、`thread_id: str`、`tenant_id: str`、`intent: str`、`awaiting_human: bool`。
`thread_id`（checkpointer 持久化主键 / 时间旅行回放键）与 `tenant_id`（多租户隔离）后续任务使用。

### `llm.py` — `FakeLLM`
与 sql-self-healer 同接口：`__init__(script: list[str])`、`generate(prompt) -> str`，
按顺序返回脚本项；耗尽后返回最后一项；空脚本抛 `ValueError`。

### `checkpoint.py` — `make_checkpointer(db_path="checkpoints.db")`
- 默认/文件路径/sqlite 前缀 → `SqliteSaver.from_conn_string(db_path)`。
- `postgresql://` 前缀 → 尝试 `from langgraph.checkpoint.postgres import PostgresSaver`；
  未安装则抛带中文提示的 `ImportError`（postgres 不作硬依赖）。
- 返回的 saver 由进程级 `contextlib.ExitStack` 保活——底层 sqlite3 连接常驻，
  直到 `close_all()` 或解释器退出；文档注明「调用方拥有关闭责任」。

## TDD 证据

### 1) 先写测试 → FAIL（实现未建）
```
$ python -m pytest tests/test_checkpoint.py -q
ERROR collecting tests/test_checkpoint.py
E   ModuleNotFoundError: No module named 'saas_cs_agent.checkpoint'
1 error in 0.24s
```

### 2) 实现后 → PASS
```
$ python -m pytest tests/test_checkpoint.py -q
....                                                                     [100%]
4 passed in 0.16s
```
测试用例：`test_state_defaults` / `test_fake_llm_returns_scripted` /
`test_make_checkpointer_returns_sqlite_saver`（断言 `isinstance(saver, BaseCheckpointSaver)`）/
`test_make_checkpointer_postgres_without_pkg_raises`（包已装则跳过断言）。

### 3) 全量 `pytest -q`
```
$ python -m pytest -q
....                                                                     [100%]
4 passed in 0.16s
```

## 环境
- Python 3.10.6（满足 `>=3.10`）
- langgraph 1.2.6（已装，满足 `>=1.2`）
- langgraph-checkpoint-sqlite **3.1.0**（`pip install "langgraph-checkpoint-sqlite>=2.0"` 解析到的实际版本；>=2.0 满足）
- langgraph-checkpoint-postgres **未安装**（符合「可选依赖」定位；测试用例相应跳过断言）
- 无 API Key、无 Docker、无网络（FakeLLM + sqlite 闭环）

## Commit
```
0f4f663 feat(cs-agent): 仓骨架 + CSState + SqliteSaver checkpointer + FakeLLM
```
（11 文件全进，无 *.db 泄漏；CRLF 警告为 Windows 正常行为。）

## 关注点 / 注意事项

1. **`langgraph-checkpoint-sqlite` 实际装到 3.1.0**：spec 写 `>=2.0`，pip 解析到
   3.1.0（当前最新）。`SqliteSaver.from_conn_string` 仍存在且返回
   `Iterator[SqliteSaver]`（上下文管理器风格工厂），`SqliteSaver` 仍是
   `BaseCheckpointSaver` 子类——接口与 spec 假设一致，未踩坑。若后续要锁版本，
   建议 `langgraph-checkpoint-sqlite>=2.0,<4`。

2. **`from_conn_string` 是上下文管理器工厂，不是普通函数**：直接 `return SqliteSaver.from_conn_string(db_path)`
   会返回一个生成器对象而非 saver，且未进入上下文 → 连接未打开。本实现用进程级
   `ExitStack.enter_context(...)` 同时完成「进入上下文」与「保活连接」两件事。
   长驻进程需在停机时调用 `close_all()`；测试进程短，可不调用。

3. **进程级单栈设计**：`_stack` 是模块级全局，所有 `make_checkpointer` 调用共享。
   对单进程多 saver 场景够用；若未来要做热替换/并发隔离，需重构为每实例独立栈。

4. **postgres 路径未实跑**：本地未装 `langgraph-checkpoint-postgres`，只验证了
   「未装时抛 ImportError」分支；真实 PostgresSaver 的 `from_conn_string` 假设其
   同为上下文管理器风格工厂（与 SqliteSaver 一致），若 1.2.x 下签名不同需在后续
   postgres 任务里修正 `_enter_context` 适配。

5. **范围控制**：仅交付 foundation（state/checkpoint/llm + 测试 + 配置/文档），
   未触碰 tenant 隔离逻辑、nodes、graph、time_travel —— 留给后续任务。

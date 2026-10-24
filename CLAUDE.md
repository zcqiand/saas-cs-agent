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

## 正式区 / 临时区（2026-10-24 人定，全产品线通用）

- 过程件不与正式件混放：任务卡/批次卡、片段（frags-*）、批次文件、合并/对账/自检脚本、门控回执（receipts-*）、调试日志、QC 抽帧——项目级进 `_work/`，章级/集级进所属正式目录下 `_work/` 子目录
- 正式区同名正式件有且仅有一个（不堆 v2/final 副本）
- 章节正文、章级门控记录（chapter-NNN.*）、各类台账 json 是正式件，不进 `_work`
- 可再生件不入库（见 .gitignore）：node_modules、build、out、bin/obj、`**/_work/render`、hook 审计日志

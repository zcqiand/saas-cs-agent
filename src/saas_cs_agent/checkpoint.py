"""Checkpointer 工厂。

按 ``db_path`` 协议前缀选择后端：

- 默认（文件路径或 ``sqlite://``）→ ``SqliteSaver``（``langgraph-checkpoint-sqlite``）
- ``postgresql://`` → ``PostgresSaver``（需额外安装 ``langgraph-checkpoint-postgres``，
  不作为硬依赖；未装时抛出带提示信息的 ``ImportError``）

返回的 saver 是一个长期持有底层连接的「进程级」实例：调用方拥有其生命周期，
进程退出前应显式关闭（见模块 ``__all__`` 下方的 ``close_all``）。

「时间旅行」能力（回到某 ``thread_id`` 的历史 checkpoint）由 LangGraph 的
``BaseCheckpointSaver`` 接口直接提供，无需本仓额外实现。
"""

from __future__ import annotations

import contextlib
from typing import Iterator

_DEFAULT_SQLITE_PATH = "checkpoints.db"
# 进程级 ExitStack：持有所有已建 saver 的上下文，使底层 sqlite3 连接常驻，
# 直到调用方显式 close_all() 或解释器退出。本仓测试进程生命周期短，
# 通常无需手动关闭。
_stack: contextlib.ExitStack | None = None


def _get_stack() -> contextlib.ExitStack:
    global _stack
    if _stack is None:
        _stack = contextlib.ExitStack()
    return _stack


def close_all() -> None:
    """关闭所有由 ``make_checkpointer`` 创建的 saver 及其底层连接。

    通常只在长驻进程的优雅停机阶段调用；测试进程可不调用。
    """
    global _stack
    if _stack is not None:
        _stack.close()
        _stack = None


def make_checkpointer(db_path: str = _DEFAULT_SQLITE_PATH):
    """创建并返回一个 checkpointer 实例。

    Parameters
    ----------
    db_path:
        - 默认 ``"checkpoints.db"`` 或任意文件路径 / ``sqlite://`` 前缀 →
          返回 ``SqliteSaver``。
        - 以 ``postgresql://`` 开头 → 尝试返回 ``PostgresSaver``；若
          ``langgraph-checkpoint-postgres`` 未安装则抛出带提示的 ``ImportError``。

    Returns
    -------
    BaseCheckpointSaver
        已初始化、底层连接保持打开的 saver 实例。**调用方拥有其生命周期**——
        进程退出前应调用 :func:`close_all`（或自行管理）以释放连接。

    Notes
    -----
    ``SqliteSaver.from_conn_string`` 是一个上下文管理器风格的工厂（在
    langgraph 1.2.x / langgraph-checkpoint-sqlite 2.x+ 中返回
    ``Iterator[SqliteSaver]``）。这里通过一个进程级 ``ExitStack`` 进入其
    上下文、取出它 yield 出来的 saver，并让连接在进程生命周期内常驻。
    """
    if db_path.startswith("postgresql://"):
        try:
            from langgraph.checkpoint.postgres import PostgresSaver  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - 取决于可选依赖是否安装
            raise ImportError(
                "需要 'langgraph-checkpoint-postgres' 才能使用 PostgresSaver。"
                "请运行 `pip install langgraph-checkpoint-postgres`，或改用 SQLite（默认）。"
            ) from exc
        # PostgresSaver 同样是上下文管理器风格工厂；按需实例化。
        return _enter_context(PostgresSaver.from_conn_string(db_path))

    # SQLite 路径（默认）
    from langgraph.checkpoint.sqlite import SqliteSaver

    return _enter_context(SqliteSaver.from_conn_string(db_path))


def _enter_context(factory: Iterator):
    """进入一个上下文管理器风格的工厂，返回其产物，并由进程级栈保活。"""
    stack = _get_stack()
    return stack.enter_context(factory)


__all__ = ["make_checkpointer", "close_all"]

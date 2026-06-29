"""LangGraph 全局状态定义。

``CSState`` 在各客服节点间传递：对话消息历史、线程/租户隔离标识、
当前意图分类、是否需要人工接管标志。

多租户隔离与「时间旅行」回放都依赖 ``thread_id``（对话线程唯一键，
被 checkpointer 用作持久化主键）与 ``tenant_id``（租户隔离）。
"""

from __future__ import annotations

from typing import TypedDict


class CSState(TypedDict):
    """客服 Agent 各节点共享的全局状态。"""

    messages: list
    thread_id: str
    tenant_id: str
    intent: str
    awaiting_human: bool


__all__ = ["CSState"]

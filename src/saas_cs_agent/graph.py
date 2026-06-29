"""客服图装配。

``build_graph`` 用 ``StateGraph(CSState)`` 串起四个节点：

    START → classify_intent → retrieve_kb → compose_reply → human_review → END

并在 ``human_review`` 之前设置 ``interrupt_before``，从而在生成回复后、
人工放行前暂停——这就是 HITL（Human-In-The-Loop）介入点。

恢复语义（langgraph 1.2.x）：暂停后再次以
``invoke(None, config)`` 调用同一图，会从断点之后继续执行，最终到达
``END``。``checkpointer`` 负责把每个节点的输出落盘，使暂停/恢复跨调用
可用、且按 ``thread_id`` 隔离。
"""

from __future__ import annotations

import functools
from typing import Any

from langgraph.graph import END, START, StateGraph

from saas_cs_agent.nodes import (
    classify_intent,
    compose_reply,
    human_review,
    retrieve_kb,
)
from saas_cs_agent.state import CSState


def build_graph(checkpointer: Any, llm: Any):
    """装配并返回带 HITL 中断的客服 CompiledGraph。

    Parameters
    ----------
    checkpointer:
        已初始化的 ``BaseCheckpointSaver``（如 ``SqliteSaver``），
        用于按 ``thread_id`` 持久化与恢复图状态。
    llm:
        注入到需要生成能力的节点（``classify_intent``、``compose_reply``）
        中的 LLM；测试时传 ``FakeLLM``。

    Returns
    -------
    CompiledGraph
        已编译、绑定 checkpointer、在 ``human_review`` 前 interrupt 的图。
    """
    graph = StateGraph(CSState)

    # 用 functools.partial 把 llm 绑定到需要它的节点；retrieve_kb 与
    # human_review 无需额外依赖，直接挂函数。
    graph.add_node("classify_intent", functools.partial(classify_intent, llm=llm))
    graph.add_node("retrieve_kb", retrieve_kb)
    graph.add_node("compose_reply", functools.partial(compose_reply, llm=llm))
    graph.add_node("human_review", human_review)

    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "retrieve_kb")
    graph.add_edge("retrieve_kb", "compose_reply")
    graph.add_edge("compose_reply", "human_review")
    graph.add_edge("human_review", END)

    return graph.compile(
        interrupt_before=["human_review"],
        checkpointer=checkpointer,
    )


__all__ = ["build_graph"]

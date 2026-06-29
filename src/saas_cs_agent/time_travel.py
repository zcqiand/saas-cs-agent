"""时间旅行：历史回溯 + 分叉重放。

LangGraph 的 ``BaseCheckpointSaver`` 把每个节点执行后的状态按
``thread_id`` 落盘成一条 checkpoint 链。本模块在 checkpointer 之上提供
两个薄封装，对应「时间旅行」的两类用法：

- :func:`list_history` —— 列出某 ``thread_id`` 的全部历史快照
  （``StateSnapshot``），用于审计 / 回看「这个会话是怎么一步步走到这里」。
- :func:`fork_from` —— 从某个历史 checkpoint 起、用一个**新的输入**在
  **另一条 thread** 上重放，得到一条与原会话分叉的执行轨迹。典型场景：
  发现某客服对话在早期意图分类处就走偏，想用不同的话术重新尝试。

分叉语义（langgraph 1.2.x）
---------------------------
``fork_from`` 把 ``checkpoint_id`` 与一个新的 ``fork_thread_id`` 一起放进
``config["configurable"]``，再以 ``new_input`` 调用 ``graph.invoke``。LangGraph
据此在新 thread 上从指定历史 checkpoint 起步、用新输入推进，因此新轨迹与
原 thread 互不干扰——这正是「时间旅行 + 分叉」。

NOTE: 1.2.x 的 ``get_state_history`` 按时间倒序 yield 快照，即 ``list_history``
返回的列表 ``[0]`` 是最新、``[-1]`` 是最早。
"""

from __future__ import annotations

from typing import Any


def list_history(graph: Any, thread_id: str) -> list:
    """返回某 ``thread_id`` 的历史 ``StateSnapshot`` 列表。

    直接消费 ``graph.get_state_history``，并物化为列表，方便测试取
    ``config["configurable"]["checkpoint_id"]`` 与 ``.values``。

    Parameters
    ----------
    graph:
        已绑定 checkpointer 的 CompiledGraph。
    thread_id:
        要回看的对话线程键。

    Returns
    -------
    list[StateSnapshot]
        历史快照列表，**最新在前**（与 ``get_state_history`` 的 yield
        顺序一致），因此 ``[-1]`` 是最早的 checkpoint。
    """
    return list(
        graph.get_state_history({"configurable": {"thread_id": thread_id}})
    )


def fork_from(
    graph: Any,
    checkpoint_id: str,
    new_input: dict,
    fork_thread_id: str,
) -> dict:
    """从历史 checkpoint 起在新 thread 上分叉重放。

    构造 ``config = {"configurable": {"thread_id": fork_thread_id,
    "checkpoint_id": checkpoint_id}}``，以 ``new_input`` 调用
    ``graph.invoke``。新轨迹运行在独立的 ``fork_thread_id`` 下，与原
    thread 隔离、互不影响。

    Parameters
    ----------
    graph:
        已绑定 checkpointer 的 CompiledGraph。
    checkpoint_id:
        要回溯到的历史 checkpoint（取自 ``list_history`` 中某快照的
        ``config["configurable"]["checkpoint_id"]``）。
    new_input:
        用于驱动分叉执行的全新输入（覆盖该 checkpoint 处的状态）。
    fork_thread_id:
        分叉轨迹使用的独立线程键。

    Returns
    -------
    dict
        ``graph.invoke(new_input, config)`` 的最终状态。
    """
    config = {
        "configurable": {
            "thread_id": fork_thread_id,
            "checkpoint_id": checkpoint_id,
        }
    }
    return graph.invoke(new_input, config)


__all__ = ["list_history", "fork_from"]

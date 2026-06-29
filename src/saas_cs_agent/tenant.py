"""多租户线程隔离。

LangGraph 的 checkpointer 用 ``thread_id`` 作为持久化主键——要实现多租户
隔离，只需让每个 (租户, 会话) 组合映射到唯一的 ``thread_id``。这里采用
``"{tenant_id}:{session_id}"`` 这一可读且无歧义的格式：

- 同一租户的不同会话 → 不同 ``thread_id``（会话隔离）
- 不同租户的相同会话 ID → 不同 ``thread_id``（租户隔离，杜绝跨租户串话）

``TenantRouter`` 在此基础上提供一个进程内的注册表：把某次会话的
``thread_id`` 记下来，后续任意节点都能凭 (租户, 会话) 取回同一条线程，
从而支撑「人工接管后回到原线程继续」等流程。
"""

from __future__ import annotations


def thread_id_for(tenant_id: str, session_id: str) -> str:
    """返回 (租户, 会话) 对应的唯一 thread_id。

    格式 ``"{tenant_id}:{session_id}"``：可读、可解析，且天然保证
    不同租户或不同会话得到不同的 ``thread_id``。
    """
    return f"{tenant_id}:{session_id}"


class TenantRouter:
    """进程内的 (租户, 会话) → thread_id 注册表。

    ``register`` 为一对 (租户, 会话) 显式登记一个 ``thread_id``（由
    :func:`thread_id_for` 生成）并返回；``get_thread`` 优先返回已登记的
    值，若该组合从未登记则即时构建一个（保证调用方总能拿到稳定的
    ``thread_id``，不因登记顺序差异而漂移）。
    """

    def __init__(self) -> None:
        # 内部映射：(tenant_id, session_id) -> thread_id
        self._threads: dict[tuple[str, str], str] = {}

    def register(self, tenant_id: str, session_id: str) -> str:
        """登记并返回 (租户, 会话) 的 thread_id。

        重复登记同一组合是幂等的：始终返回由 :func:`thread_id_for` 派生
        的同一值（格式确定，无随机性）。
        """
        tid = thread_id_for(tenant_id, session_id)
        self._threads[(tenant_id, session_id)] = tid
        return tid

    def get_thread(self, tenant_id: str, session_id: str) -> str:
        """返回 (租户, 会话) 的 thread_id。

        已登记则返回存储值；未登记则即时构建并返回（不写入注册表，
        保持 ``register`` 的显式语义）。
        """
        stored = self._threads.get((tenant_id, session_id))
        if stored is not None:
            return stored
        return thread_id_for(tenant_id, session_id)


__all__ = ["thread_id_for", "TenantRouter"]

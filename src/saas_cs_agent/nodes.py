"""LangGraph 客服节点函数。

每个节点接收当前 ``CSState``（以及所需依赖，如 ``llm``），返回一个
**部分状态字典**——LangGraph 会把它合并进全局状态。

关于 ``messages`` 的合并语义：``CSState.messages`` 在 ``state.py`` 中声明
为普通 ``list``（未使用 ``add_messages`` reducer），因此默认是「整体覆写」。
为了让追加的消息真正进入状态，节点显式返回
``state["messages"] + [新消息]``，用扩展后的列表覆写旧列表——这是一种
不依赖 reducer 的就地追加模式，简单且对 FakeLLM 测试透明。
"""

from __future__ import annotations

from typing import Any

from saas_cs_agent.state import CSState

# 硬编码的迷你知识库：意图关键字 → 回复片段。
# 真实系统会接入向量检索；这里用字典演示 retrieve_kb 的契约。
_KB: dict[str, str] = {
    "password_reset": "密码重置：访问 /reset，输入注册邮箱",
    "billing": "账单：登录后「账单」页查看",
    "faq": "常见问题：见帮助中心",
}


def classify_intent(state: CSState, llm: Any) -> dict:
    """用 LLM 对最新一条用户消息做意图分类。

    prompt 取 ``messages`` 中最后一条 ``role=user`` 的内容；分类结果写入
    ``intent`` 字段，供下游 ``retrieve_kb`` 选择知识片段。
    """
    prompt = ""
    for msg in reversed(state.get("messages", [])):
        if msg.get("role") == "user":
            prompt = msg.get("content", "")
            break
    intent = llm.generate(prompt)
    return {"intent": intent}


def retrieve_kb(state: CSState) -> dict:
    """按当前意图从迷你知识库取一条片段，作为 system 消息追加。

    匹配策略：把 ``intent`` 作为子串/关键字在 KB 键中查找；命中则用对应
    片段，否则回落到 ``"faq"``。返回扩展后的 ``messages``（覆写语义）。
    """
    intent = state.get("intent", "") or ""
    snippet = _KB["faq"]
    for key, value in _KB.items():
        if key in intent or intent in key:
            snippet = value
            break
    new_messages = list(state.get("messages", [])) + [
        {"role": "system", "content": snippet}
    ]
    return {"messages": new_messages}


def compose_reply(state: CSState, llm: Any) -> dict:
    """用 LLM 基于上下文生成最终回复，作为 assistant 消息追加。"""
    # 把 messages 中的内容串成上下文喂给 LLM；FakeLLM 不真正解析它，
    # 真实 LLM 会据此生成更有针对性的回复。
    context_parts = [
        f"{m.get('role', '')}: {m.get('content', '')}"
        for m in state.get("messages", [])
    ]
    context = "\n".join(context_parts)
    reply = llm.generate(context)
    new_messages = list(state.get("messages", [])) + [
        {"role": "assistant", "content": reply}
    ]
    return {"messages": new_messages}


def human_review(state: CSState) -> dict:  # noqa: ARG001 - state 在此节点仅作占位
    """人工复核节点。

    图在到达本节点 *之前* 被 ``interrupt_before`` 暂停，等待人工介入；
    本节点在恢复后执行，标记 ``awaiting_human=False`` 表示复核完成、
    可以流向 END。
    """
    return {"awaiting_human": False}


__all__ = ["classify_intent", "retrieve_kb", "compose_reply", "human_review"]

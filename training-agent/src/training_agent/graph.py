"""LangGraph ReAct agent for the Soofi Training Agent."""

import logging
import os

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode

from .prompts import SYSTEM_PROMPT_DE

logger = logging.getLogger(__name__)

model = os.getenv("INTERACTION_MODEL")
if not model:
    raise RuntimeError("INTERACTION_MODEL env var required.")


def build_graph(tools: list[BaseTool]) -> CompiledStateGraph:
    """Build the LangGraph ReAct agent with the given tools."""
    llm = ChatOpenAI(model=model).bind_tools(tools, parallel_tool_calls=False)
    tool_node = ToolNode(tools)

    async def agent(state: MessagesState, config: RunnableConfig) -> MessagesState:
        prompt = config.get("configurable", {}).get("system_prompt", SYSTEM_PROMPT_DE)
        system = {"role": "system", "content": prompt}
        response = await llm.ainvoke([system] + state["messages"])
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                logger.info(f"Tool call: {tc['name']}({tc['args']})")
        return {"messages": [response]}

    async def log_tool_results(state: MessagesState) -> MessagesState:
        result = await tool_node.ainvoke(state)
        for msg in result["messages"]:
            logger.info(f"Tool result ({msg.name}): {str(msg.content)[:500]}")
        return result

    def should_continue(state: MessagesState) -> str:
        if not state["messages"]:
            return "__end__"
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "__end__"

    graph_builder = StateGraph(MessagesState)
    graph_builder.add_node("agent", agent)
    graph_builder.add_node("tools", log_tool_results)
    graph_builder.set_entry_point("agent")
    graph_builder.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", "__end__": "__end__"}
    )
    graph_builder.add_edge("tools", "agent")

    memory = MemorySaver()
    return graph_builder.compile(checkpointer=memory)

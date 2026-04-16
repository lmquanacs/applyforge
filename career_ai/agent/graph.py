from __future__ import annotations

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

from career_ai.agent.state import AgentState
from career_ai.agent.nodes import (
    node_extract_jd,
    node_fix_extraction,
    node_ats_score,
    node_vault_query,
    node_generate_cv,
    node_generate_cover_letter,
    node_generate_interview_prep,
    node_summarise,
    should_retry_extraction,
)


def build_graph(db_path: str | None = None):
    """
    Compile the Auto-Apply LangGraph pipeline.
    Pass db_path to enable SQLite checkpointing (resumable runs).
    """
    builder = StateGraph(AgentState)

    builder.add_node("extract_jd", node_extract_jd)
    builder.add_node("fix_extraction", node_fix_extraction)
    builder.add_node("ats_score", node_ats_score)
    builder.add_node("vault_query", node_vault_query)
    builder.add_node("generate_cv", node_generate_cv)
    builder.add_node("generate_cover_letter", node_generate_cover_letter)
    builder.add_node("generate_interview_prep", node_generate_interview_prep)
    builder.add_node("summarise", node_summarise)

    builder.set_entry_point("extract_jd")

    # Conditional edge: retry extraction once on failure
    builder.add_conditional_edges(
        "extract_jd",
        should_retry_extraction,
        {"retry": "fix_extraction", "continue": "ats_score"},
    )
    builder.add_edge("fix_extraction", "ats_score")
    builder.add_edge("ats_score", "vault_query")
    builder.add_edge("vault_query", "generate_cv")
    builder.add_edge("generate_cv", "generate_cover_letter")
    builder.add_edge("generate_cover_letter", "generate_interview_prep")
    builder.add_edge("generate_interview_prep", "summarise")
    builder.add_edge("summarise", END)

    if db_path:
        import sqlite3
        conn = sqlite3.connect(db_path, check_same_thread=False)
        checkpointer = SqliteSaver(conn)
        return builder.compile(checkpointer=checkpointer)

    return builder.compile()

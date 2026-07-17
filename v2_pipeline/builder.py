"""
Constructeur de graphe amélioré pour le pipeline V2
- Même structure que V1 pour compatibilité
- Support des checkpoints (prêt pour extension future)
"""
from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    load_data_node,
    create_batches_node,
    process_batch_node,
    save_results_node,
)


def should_continue(state: AgentState) -> str:
    """Retourne vers process_batch tant qu'il reste des lots non traités."""
    if state["current_batch_index"] < len(state["batches"]):
        return "process_batch"
    return "save_results"


def build_graph() -> StateGraph:
    """Construit et retourne le graphe LangGraph avec boucle de traitement."""
    workflow = StateGraph(AgentState)

    workflow.add_node("load_data", load_data_node)
    workflow.add_node("create_batches", create_batches_node)
    workflow.add_node("process_batch", process_batch_node)
    workflow.add_node("save_results", save_results_node)

    workflow.set_entry_point("load_data")
    workflow.add_edge("load_data", "create_batches")
    workflow.add_edge("create_batches", "process_batch")

    # Boucle conditionnelle : traite tous les lots avant de sauvegarder
    workflow.add_conditional_edges(
        "process_batch",
        should_continue,
        {"process_batch": "process_batch", "save_results": "save_results"},
    )

    workflow.add_edge("save_results", END)

    return workflow.compile()

"""
État partagé amélioré pour le pipeline V2
- Support des checkpoints
- Métadonnées de progression
- Sérialisation pour sauvegarde
"""
from typing import TypedDict, List, Optional, Any
import pandas as pd
import json


class AgentState(TypedDict):
    """
    État partagé entre les nœuds du graphe avec support amélioré.
    """
    # Configuration
    input_file: str
    output_file: str
    model_key: str
    batch_size: int
    mission_config: dict
    
    # Données
    dataframe: Optional[pd.DataFrame]
    batches: List[dict]
    
    # Progression
    current_batch_index: int
    results: List[dict]
    errors: List[str]
    status: str  # "pending", "processing", "completed", "failed"
    
    # Métadonnées pour checkpoints
    checkpoint_data: Optional[dict]
    processed_count: int
    failed_count: int
    
    # Configuration avancée
    llm_config: Optional[dict]
    validation_config: Optional[dict]
    save_config: Optional[dict]


def state_to_dict(state: AgentState) -> dict:
    """
    Convertit l'état en dictionnaire sérialisable pour sauvegarde.
    """
    serializable = dict(state)
    
    # Convertir le DataFrame en JSON si présent
    if serializable.get("dataframe") is not None:
        serializable["dataframe"] = {
            "columns": serializable["dataframe"].columns.tolist(),
            "data": serializable["dataframe"].values.tolist()
        }
    
    return serializable


def dict_to_state(data: dict) -> AgentState:
    """
    Reconstruit un état depuis un dictionnaire sérialisé.
    """
    state = data.copy()
    
    # Reconstruire le DataFrame si présent
    if state.get("dataframe") and isinstance(state["dataframe"], dict):
        df_data = state["dataframe"]
        state["dataframe"] = pd.DataFrame(
            df_data["data"],
            columns=df_data["columns"]
        )
    
    return state

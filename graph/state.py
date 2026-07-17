from typing import TypedDict, List, Optional
import pandas as pd


class AgentState(TypedDict):
    """État partagé entre les nœuds du graphe."""
    input_file: str
    output_file: str
    model_key: str
    batch_size: int
    dataframe: Optional[pd.DataFrame]
    batches: List[dict]
    current_batch_index: int
    results: List[dict]
    errors: List[str]
    status: str  # "pending", "processing", "completed", "failed"
    mission_config: dict  # Configuration complète de la mission
import os
import re
from langchain_openai import ChatOpenAI
from graph.state import AgentState
from utils.tsv_handler import read_tsv, write_tsv
from utils.batcher import create_batches, get_mission_columns


def load_data_node(state: AgentState) -> AgentState:
    """Charge le fichier TSV en DataFrame."""
    try:
        df = read_tsv(state["input_file"])
        state["dataframe"] = df
        state["status"] = "processing"
        print(f"[LOAD] {len(df)} lignes chargées depuis {state['input_file']}")
    except Exception as e:
        state["status"] = "failed"
        state["errors"].append(f"Load error: {str(e)}")
        print(f"[LOAD ERROR] {e}")
    return state


def create_batches_node(state: AgentState) -> AgentState:
    """Découpe le DataFrame en lots selon la config de la mission."""
    if state["dataframe"] is None:
        state["status"] = "failed"
        state["errors"].append("No dataframe to batch")
        return state

    mission_name = state["mission_config"].get("mission_name", "exemple_mission")
    mission_dir = os.path.join("missions", mission_name)
    
    batches = create_batches(state["dataframe"], state["batch_size"], mission_dir)
    state["batches"] = batches
    state["current_batch_index"] = 0
    state["results"] = []
    print(f"[BATCH] {len(batches)} lots créés (taille={state['batch_size']})")
    return state


def process_batch_node(state: AgentState) -> AgentState:
    """Traite un lot avec l'API Requesty via OpenAI-compatible."""
    idx = state["current_batch_index"]
    if idx >= len(state["batches"]):
        state["status"] = "completed"
        return state

    batch = state["batches"][idx]
    config = state["mission_config"]
    mission_name = config.get("mission_name", "exemple_mission")
    mission_dir = os.path.join("missions", mission_name)

    # Chargement du prompt système
    prompt_path = os.path.join(mission_dir, "prompt.txt")
    system_prompt = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()

    api_key = os.environ.get("REQUESTY_API_KEY", "")
    llm = ChatOpenAI(
        model=config.get("model_name", "deepseek/deepseek-chat"),
        temperature=config.get("temperature", 0.1),
        max_tokens=config.get("max_tokens", 4000),
        openai_api_base="https://router.requesty.ai/v1",
        openai_api_key=api_key,
    )

    try:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": batch["text"]})

        response = llm.invoke(messages)
        text_content = response.content if hasattr(response, 'content') else str(response)
        
        state["results"].append({"response": text_content, "batch_idx": idx})
        print(f"[DEBUG] Réponse LLM : {text_content[:300]}...")
        print(f"[PROCESS] Lot {idx} traité")
    except Exception as e:
        state["errors"].append(f"Batch {idx}: {str(e)}")
        print(f"[PROCESS ERROR] Lot {idx}: {e}")

    state["current_batch_index"] += 1
    return state


def clean_field(value: str) -> str:
    """Nettoie une chaîne pour qu'elle tienne sur une seule ligne."""
    if not value: return ""
    cleaned = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def save_results_node(state: AgentState) -> AgentState:
    """Sauvegarde les résultats en TSV de manière dynamique."""
    try:
        if state["results"]:
            mission_name = state["mission_config"].get("mission_name", "exemple_mission")
            mission_dir = os.path.join("missions", mission_name)
            _, output_cols = get_mission_columns(mission_dir)
            
            final_data = []
            
            for res in state["results"]:
                text = res.get("response", "")
                
                # Découpage sur ###EVAL###
                evaluations = text.split("###EVAL###")
                
                for eval_text in evaluations:
                    if not eval_text.strip(): continue
                    
                    # On initialise la ligne avec les colonnes de ton columns.txt
                    row = {col: "" for col in output_cols}
                    found_data = False
                    
                    for col in output_cols:
                        # Recherche dynamique : "Nom_Colonne: Valeur"
                        # Gère aussi le cas où le LLM écrit "segment_id: 1001"
                        pattern = rf"{col}\s*[:：]\s*(.*)"
                        match = re.search(pattern, eval_text, re.IGNORECASE)
                        
                        if match:
                            row[col] = clean_field(match.group(1))
                            found_data = True
                    
                    if found_data:
                        final_data.append(row)

            write_tsv(final_data, state["output_file"])
            print(f"[SAVE] {len(final_data)} évaluations sauvegardées dans {state['output_file']}")
        state["status"] = "completed"
    except Exception as e:
        state["status"] = "failed"
        state["errors"].append(f"Save error: {str(e)}")
        print(f"[SAVE ERROR] {e}")
    return state
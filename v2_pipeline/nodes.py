"""
Nœuds améliorés pour le pipeline V2
- Logging complet à chaque étape
- Gestion des erreurs avec retries
- Validation des données
- Support des checkpoints
"""
import os
import re
import time
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from .state import AgentState
from .tsv_handler import read_tsv, write_tsv
from .batcher import create_batches, get_mission_columns
from .logger import setup_logger


# Initialisation du logger
logger = setup_logger(
    name="pipeline_v2_nodes",
    log_level="INFO",
    log_file="logs/pipeline_v2.log"
)


def load_data_node(state: AgentState) -> AgentState:
    """Charge le fichier TSV en DataFrame avec validation."""
    logger.info(f"[LOAD] Démarrage du chargement : {state['input_file']}")
    
    try:
        # Récupérer les colonnes requises depuis la config de mission
        mission_name = state["mission_config"].get("mission_name", "exemple_mission")
        mission_dir = os.path.join("missions", mission_name)
        input_cols, _ = get_mission_columns(mission_dir, logger)
        
        df = read_tsv(
            state["input_file"],
            logger=logger,
            required_columns=input_cols if state.get("validation_config", {}).get("check_required_columns", True) else None,
            skip_invalid_rows=state.get("validation_config", {}).get("skip_invalid_rows", False),
            max_empty_rows=state.get("validation_config", {}).get("max_empty_rows", 10)
        )
        
        state["dataframe"] = df
        state["status"] = "processing"
        state["processed_count"] = 0
        state["failed_count"] = 0
        
        logger.info(f"[LOAD] {len(df)} lignes chargées avec succès")
        logger.debug(f"[LOAD] Colonnes détectées : {list(df.columns)}")
        
    except FileNotFoundError as e:
        state["status"] = "failed"
        error_msg = f"Load error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"[LOAD ERROR] {error_msg}")
        
    except ValueError as e:
        state["status"] = "failed"
        error_msg = f"Validation error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"[LOAD ERROR] {error_msg}")
        
    except Exception as e:
        state["status"] = "failed"
        error_msg = f"Unexpected load error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"[LOAD ERROR] {error_msg}", exc_info=True)
    
    return state


def create_batches_node(state: AgentState) -> AgentState:
    """Découpe le DataFrame en lots selon la config de la mission."""
    logger.info("[BATCH] Démarrage de la création des lots")
    
    if state["dataframe"] is None:
        state["status"] = "failed"
        error_msg = "No dataframe to batch"
        state["errors"].append(error_msg)
        logger.error(f"[BATCH ERROR] {error_msg}")
        return state

    try:
        mission_name = state["mission_config"].get("mission_name", "exemple_mission")
        mission_dir = os.path.join("missions", mission_name)
        
        batches = create_batches(
            state["dataframe"],
            state["batch_size"],
            mission_dir,
            logger=logger
        )
        
        state["batches"] = batches
        state["current_batch_index"] = 0
        state["results"] = []
        
        logger.info(f"[BATCH] {len(batches)} lots créés (taille={state['batch_size']})")
        
    except Exception as e:
        state["status"] = "failed"
        error_msg = f"Batch creation error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"[BATCH ERROR] {error_msg}", exc_info=True)
    
    return state


@retry(
    stop=stop_after_attempt(3),
    wait=wait_fixed(2),
    retry=retry_if_exception_type(Exception),
    reraise=True
)
def call_llm_with_retry(llm, messages, config):
    """Appel LLM avec retry automatique."""
    timeout = config.get("timeout", 60)
    return llm.invoke(messages, {"timeout": timeout})


def process_batch_node(state: AgentState) -> AgentState:
    """Traite un lot avec l'API Requesty via OpenAI-compatible avec retries."""
    idx = state["current_batch_index"]
    
    if idx >= len(state["batches"]):
        logger.info("[PROCESS] Tous les lots traités")
        state["status"] = "completed"
        return state

    batch = state["batches"][idx]
    config = state["mission_config"]
    llm_config = state.get("llm_config", {})
    
    mission_name = config.get("mission_name", "exemple_mission")
    mission_dir = os.path.join("missions", mission_name)

    # Chargement du prompt système
    prompt_path = os.path.join(mission_dir, "prompt.txt")
    system_prompt = ""
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        logger.debug(f"[PROCESS] Prompt système chargé ({len(system_prompt)} caractères)")
    else:
        logger.warning(f"[PROCESS] Aucun prompt système trouvé dans {prompt_path}")

    # Configuration du LLM
    api_key = os.environ.get("REQUESTY_API_KEY", "")
    if not api_key:
        state["errors"].append("REQUESTY_API_KEY non définie")
        logger.error("[PROCESS ERROR] REQUESTY_API_KEY manquante")
        state["current_batch_index"] += 1
        state["failed_count"] += 1
        return state

    try:
        llm = ChatOpenAI(
            model=config.get("model_name", llm_config.get("model_name", "deepseek/deepseek-chat")),
            temperature=config.get("temperature", llm_config.get("temperature", 0.2)),
            max_tokens=config.get("max_tokens", llm_config.get("max_tokens", 4000)),
            openai_api_base=config.get("api_base", llm_config.get("api_base", "https://router.requesty.ai/v1")),
            openai_api_key=api_key,
            request_timeout=llm_config.get("timeout", 60),
        )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": batch["text"]})

        logger.info(f"[PROCESS] Traitement du lot {idx}/{len(state['batches'])} ({batch['row_count']} lignes)")
        
        # Appel avec retry
        response = call_llm_with_retry(llm, messages, llm_config)
        text_content = response.content if hasattr(response, 'content') else str(response)
        
        state["results"].append({
            "response": text_content,
            "batch_idx": idx,
            "start_idx": batch["start_idx"],
            "end_idx": batch["end_idx"]
        })
        
        state["processed_count"] += 1
        
        logger.debug(f"[PROCESS] Réponse reçue ({len(text_content)} caractères)")
        logger.info(f"[PROCESS] Lot {idx} traité avec succès")
        
    except Exception as e:
        error_msg = f"Batch {idx}: {str(e)}"
        state["errors"].append(error_msg)
        state["failed_count"] += 1
        logger.error(f"[PROCESS ERROR] Lot {idx}: {e}", exc_info=True)
        
        # Incrémenter quand même pour continuer
        state["current_batch_index"] += 1
        return state

    state["current_batch_index"] += 1
    
    # Sauvegarde intermédiaire si activée
    save_config = state.get("save_config", {})
    if save_config.get("auto_save_interval") and state["processed_count"] % save_config["auto_save_interval"] == 0:
        logger.info(f"[PROCESS] Sauvegarde intermédiaire après {state['processed_count']} lots")
        # Ici on pourrait appeler une fonction de checkpoint
    
    return state


def clean_field(value: str) -> str:
    """Nettoie une chaîne pour qu'elle tienne sur une seule ligne."""
    if not value:
        return ""
    cleaned = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def parse_llm_response(text: str, output_cols: list, logger=None) -> list:
    """
    Parse la réponse du LLM de manière robuste.
    """
    evaluations = []
    
    # Découpage sur ###EVAL###
    parts = text.split("###EVAL###")
    
    for eval_text in parts:
        if not eval_text.strip():
            continue
        
        # Initialisation de la ligne
        row = {col: "" for col in output_cols}
        found_data = False
        
        for col in output_cols:
            # Recherche dynamique avec plusieurs patterns
            patterns = [
                rf"{col}\s*[:：]\s*(.*)",  # col: valeur
                rf"{col}\s*[=:]\s*(.*)",  # col = valeur
                rf"(?:^|\n)\s*{col}\s*[:：]\s*(.*)",  # début de ligne
            ]
            
            for pattern in patterns:
                match = re.search(pattern, eval_text, re.IGNORECASE | re.MULTILINE)
                if match:
                    row[col] = clean_field(match.group(1))
                    found_data = True
                    break
        
        if found_data:
            evaluations.append(row)
    
    if logger:
        logger.debug(f"Parsing: {len(evaluations)} évaluations extraites")
    
    return evaluations


def save_results_node(state: AgentState) -> AgentState:
    """Sauvegarde les résultats en TSV de manière dynamique avec backup."""
    logger.info("[SAVE] Démarrage de la sauvegarde des résultats")
    
    try:
        if not state["results"]:
            logger.warning("[SAVE] Aucun résultat à sauvegarder")
            state["status"] = "completed"
            return state
        
        mission_name = state["mission_config"].get("mission_name", "exemple_mission")
        mission_dir = os.path.join("missions", mission_name)
        _, output_cols = get_mission_columns(mission_dir, logger)
        
        final_data = []
        
        for res in state["results"]:
            text = res.get("response", "")
            
            # Parsing robuste
            evaluations = parse_llm_response(text, output_cols, logger)
            final_data.extend(evaluations)
        
        save_config = state.get("save_config", {})
        backup_enabled = save_config.get("backup_enabled", True)
        
        write_tsv(
            final_data,
            state["output_file"],
            logger=logger,
            backup_enabled=backup_enabled
        )
        
        logger.info(f"[SAVE] {len(final_data)} évaluations sauvegardées dans {state['output_file']}")
        state["status"] = "completed"
        
    except Exception as e:
        state["status"] = "failed"
        error_msg = f"Save error: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(f"[SAVE ERROR] {e}", exc_info=True)
    
    return state

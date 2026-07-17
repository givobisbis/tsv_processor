"""
Gestionnaire de lots (batching) amélioré pour le pipeline V2
- Validation des colonnes
- Logging détaillé
- Gestion des erreurs robuste
"""
import pandas as pd
import os
from typing import List, Tuple


def get_mission_columns(mission_dir: str, logger=None) -> Tuple[List[str], List[str]]:
    """
    Lit le fichier columns.txt en utilisant '---' comme séparateur entre entrée et sortie.
    
    Args:
        mission_dir: Chemin vers le dossier de la mission
        logger: Logger pour les messages
    
    Returns:
        Tuple (input_cols, output_cols)
    """
    col_file = os.path.join(mission_dir, "columns.txt")
    input_cols, output_cols = [], []
    section = "input"
    
    if not os.path.exists(col_file):
        warning_msg = f"Fichier columns.txt introuvable dans {mission_dir}, utilisation des valeurs par défaut"
        if logger:
            logger.warning(warning_msg)
        return ["model_input", "cleaned_model_response"], ["response"]
    
    try:
        with open(col_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                
                # Si on trouve le séparateur, on change de section
                if line == "---":
                    section = "output"
                    continue
                
                if section == "input":
                    input_cols.append(line)
                else:
                    output_cols.append(line)
        
        # Valeurs par défaut de sécurité
        if not input_cols:
            input_cols = ["model_input", "cleaned_model_response"]
            if logger:
                logger.warning("Aucune colonne d'entrée définie, utilisation des valeurs par défaut")
        if not output_cols:
            output_cols = ["response"]
            if logger:
                logger.warning("Aucune colonne de sortie définie, utilisation des valeurs par défaut")
        
        if logger:
            logger.debug(f"Colonnes d'entrée : {input_cols}")
            logger.debug(f"Colonnes de sortie : {output_cols}")
        
        return input_cols, output_cols
    
    except Exception as e:
        error_msg = f"Erreur lors de la lecture de columns.txt : {str(e)}"
        if logger:
            logger.error(error_msg)
        # Fallback aux valeurs par défaut
        return ["model_input", "cleaned_model_response"], ["response"]


def create_batches(
    df: pd.DataFrame,
    batch_size: int,
    mission_dir: str,
    logger=None
) -> List[dict]:
    """
    Découpe un DataFrame en lots en utilisant uniquement les colonnes spécifiées.
    
    Args:
        df: DataFrame à découper
        batch_size: Nombre de lignes par lot
        mission_dir: Chemin vers le dossier de la mission
        logger: Logger pour les messages
    
    Returns:
        Liste de dictionnaires contenant le texte du lot et les index
    
    Raises:
        ValueError: Si les colonnes requises sont manquantes
    """
    input_cols, _ = get_mission_columns(mission_dir, logger)
    
    if logger:
        logger.info(f"Découpage en lots de taille {batch_size} avec colonnes : {input_cols}")
    
    # Vérification que les colonnes existent bien dans le TSV
    missing_cols = [col for col in input_cols if col not in df.columns]
    if missing_cols:
        error_msg = f"Colonnes manquantes dans le TSV : {missing_cols}"
        if logger:
            logger.error(error_msg)
        raise ValueError(error_msg)
    
    batches = []
    total_rows = len(df)
    
    for i in range(0, total_rows, batch_size):
        chunk = df.iloc[i : i + batch_size][input_cols].copy()
        
        lines = []
        for _, row in chunk.iterrows():
            # On construit un texte propre pour chaque échantillon
            parts = [f"{col}: {row[col]}" for col in input_cols]
            lines.append("\n".join(parts))
        
        batch_text = "\n\n--- NEXT SAMPLE ---\n\n".join(lines)
        batches.append({
            "text": batch_text,
            "start_idx": i,
            "end_idx": min(i + batch_size, total_rows),
            "row_count": len(chunk)
        })
    
    if logger:
        logger.info(f"{len(batches)} lots créés à partir de {total_rows} lignes")
    
    return batches

import pandas as pd
import os


def get_mission_columns(mission_dir: str) -> tuple[list[str], list[str]]:
    """Lit le fichier columns.txt en utilisant '---' comme séparateur entre entrée et sortie."""
    col_file = os.path.join(mission_dir, "columns.txt")
    input_cols, output_cols = [], []
    section = "input"
    
    if not os.path.exists(col_file):
        return ["model_input", "cleaned_model_response"], ["response"]

    with open(col_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"): continue
            
            # Si on trouve le séparateur, on change de section
            if line == "---":
                section = "output"
                continue
                
            if section == "input":
                input_cols.append(line)
            else:
                output_cols.append(line)
    
    # Valeurs par défaut de sécurité
    if not input_cols: input_cols = ["model_input", "cleaned_model_response"]
    if not output_cols: output_cols = ["response"]
    
    return input_cols, output_cols


def create_batches(df: pd.DataFrame, batch_size: int, mission_dir: str) -> list[dict]:
    """Découpe un DataFrame en lots en utilisant uniquement les colonnes spécifiées."""
    input_cols, _ = get_mission_columns(mission_dir)
    
    # Vérification que les colonnes existent bien dans le TSV
    missing = [col for col in input_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes dans le TSV : {missing}")

    batches = []
    for i in range(0, len(df), batch_size):
        chunk = df.iloc[i : i + batch_size][input_cols]
        
        lines = []
        for _, row in chunk.iterrows():
            # On construit un texte propre pour chaque échantillon
            parts = [f"{col}: {row[col]}" for col in input_cols]
            lines.append("\n".join(parts))
            
        batch_text = "\n\n--- NEXT SAMPLE ---\n\n".join(lines)
        batches.append({"text": batch_text, "start_idx": i, "end_idx": i + len(chunk)})
    return batches
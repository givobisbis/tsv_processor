"""
Gestionnaire de TSV amélioré pour le pipeline V2
- Validation des colonnes requises
- Gestion des lignes vides ou invalides
- Logging des erreurs
"""
import pandas as pd
import os
from typing import List, Optional, Tuple


def read_tsv(
    filepath: str,
    logger=None,
    required_columns: Optional[List[str]] = None,
    skip_invalid_rows: bool = False,
    max_empty_rows: int = 10
) -> pd.DataFrame:
    """
    Lit un fichier TSV avec validation.
    
    Args:
        filepath: Chemin vers le fichier TSV
        logger: Logger pour les messages
        required_columns: Liste des colonnes requises
        skip_invalid_rows: Ignorer les lignes invalides au lieu de lever une erreur
        max_empty_rows: Nombre maximum de lignes vides avant erreur
    
    Returns:
        DataFrame pandas
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si les colonnes requises sont manquantes
    """
    if logger:
        logger.info(f"Lecture du fichier TSV : {filepath}")
    
    if not os.path.exists(filepath):
        error_msg = f"Fichier TSV introuvable : {filepath}"
        if logger:
            logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        df = pd.read_csv(filepath, sep="\t", dtype=str)
    except Exception as e:
        error_msg = f"Erreur lors de la lecture du TSV : {str(e)}"
        if logger:
            logger.error(error_msg)
        raise ValueError(error_msg) from e
    
    if logger:
        logger.info(f"{len(df)} lignes chargées")
    
    # Vérification des colonnes requises
    if required_columns:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            error_msg = f"Colonnes manquantes dans le TSV : {missing_cols}"
            if logger:
                logger.error(error_msg)
            raise ValueError(error_msg)
        if logger:
            logger.debug(f"Colonnes validées : {required_columns}")
    
    # Compter les lignes vides
    empty_rows = df[df.isnull().all(axis=1)].shape[0]
    if empty_rows > max_empty_rows:
        error_msg = f"Trop de lignes vides ({empty_rows} > {max_empty_rows})"
        if logger:
            logger.error(error_msg)
        if not skip_invalid_rows:
            raise ValueError(error_msg)
    
    # Supprimer les lignes complètement vides
    if skip_invalid_rows or empty_rows > 0:
        initial_count = len(df)
        df = df.dropna(how='all')
        removed_count = initial_count - len(df)
        if removed_count > 0 and logger:
            logger.warning(f"{removed_count} lignes vides supprimées")
    
    return df


def write_tsv(
    data: List[dict],
    filepath: str,
    logger=None,
    backup_enabled: bool = True
) -> None:
    """
    Écrit une liste de dictionnaires dans un fichier TSV avec sauvegarde optionnelle.
    
    Args:
        data: Liste de dictionnaires à écrire
        filepath: Chemin vers le fichier de sortie
        logger: Logger pour les messages
        backup_enabled: Créer une sauvegarde si le fichier existe déjà
    """
    if logger:
        logger.info(f"Écriture de {len(data)} enregistrements dans {filepath}")
    
    # Sauvegarde si le fichier existe déjà
    if backup_enabled and os.path.exists(filepath):
        backup_path = f"{filepath}.bak"
        try:
            os.replace(filepath, backup_path)
            if logger:
                logger.info(f"Sauvegarde créée : {backup_path}")
        except Exception as e:
            if logger:
                logger.warning(f"Impossible de créer la sauvegarde : {e}")
    
    try:
        # Créer le dossier s'il n'existe pas
        output_dir = os.path.dirname(filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            if logger:
                logger.debug(f"Dossier créé : {output_dir}")
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, sep="\t", index=False)
        
        if logger:
            logger.info(f"TSV écrit avec succès : {filepath}")
    except Exception as e:
        error_msg = f"Erreur lors de l'écriture du TSV : {str(e)}"
        if logger:
            logger.error(error_msg)
        raise ValueError(error_msg) from e

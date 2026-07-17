"""
Logger amélioré pour le pipeline V2
- Logging structuré avec niveaux
- Sauvegarde dans un fichier
- Formatage clair avec timestamps
"""
import logging
import os
from datetime import datetime


def setup_logger(
    name: str = "tsv_processor_v2",
    log_level: str = "INFO",
    log_file: str = None
) -> logging.Logger:
    """
    Configure et retourne un logger avec sortie console et fichier optionnel.
    
    Args:
        name: Nom du logger
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Chemin vers le fichier de log (optionnel)
    
    Returns:
        Logger configuré
    """
    logger = logging.getLogger(name)
    
    # Éviter d'ajouter plusieurs handlers si déjà configuré
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Format avec timestamp
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler fichier (si spécifié)
    if log_file:
        # Créer le dossier s'il n'existe pas
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logs enregistrés dans : {log_file}")
    
    return logger

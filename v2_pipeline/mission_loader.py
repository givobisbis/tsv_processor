"""
Chargement de configuration amélioré pour le pipeline V2
- Validation de la config
- Fusion avec les valeurs par défaut
- Logging des erreurs
"""
import yaml
import os
from typing import Optional


def load_mission_config(config_path: str, logger=None) -> dict:
    """
    Charge la configuration YAML d'une mission avec validation.
    
    Args:
        config_path: Chemin vers le fichier de config YAML
        logger: Logger pour les messages
    
    Returns:
        Dictionnaire de configuration
    
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        ValueError: Si la config est invalide
    """
    if logger:
        logger.info(f"Chargement de la config : {config_path}")
    
    if not os.path.exists(config_path):
        error_msg = f"Fichier de config introuvable : {config_path}"
        if logger:
            logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        # Validation des champs requis
        required_fields = ["mission_name", "input_file", "output_file"]
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            error_msg = f"Champs manquants dans la config : {missing_fields}"
            if logger:
                logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Valeurs par défaut
        config.setdefault("batch_size", 10)
        config.setdefault("model_name", "deepseek/deepseek-chat")
        config.setdefault("temperature", 0.2)
        config.setdefault("max_tokens", 4000)
        
        if logger:
            logger.info(f"Config chargée pour la mission : {config['mission_name']}")
            logger.debug(f"Paramètres : batch_size={config['batch_size']}, model={config['model_name']}")
        
        return config
    
    except yaml.YAMLError as e:
        error_msg = f"Erreur de parsing YAML : {str(e)}"
        if logger:
            logger.error(error_msg)
        raise ValueError(error_msg) from e


def load_global_config(config_path: str = None, logger=None) -> dict:
    """
    Charge la configuration globale du pipeline V2.
    
    Args:
        config_path: Chemin vers le fichier de config globale (optionnel)
        logger: Logger pour les messages
    
    Returns:
        Dictionnaire de configuration globale
    """
    # Valeurs par défaut
    default_config = {
        "general": {
            "log_level": "INFO",
            "log_file": "logs/pipeline_v2.log",
            "enable_checkpointing": False,
            "checkpoint_dir": "checkpoints/"
        },
        "llm": {
            "default_provider": "requesty",
            "api_base": "https://router.requesty.ai/v1",
            "temperature": 0.2,
            "max_tokens": 4000,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 2
        },
        "batching": {
            "default_batch_size": 10,
            "max_concurrent_batches": 1
        },
        "validation": {
            "check_required_columns": True,
            "skip_invalid_rows": False,
            "max_empty_rows": 10
        },
        "save": {
            "auto_save_interval": 5,
            "backup_enabled": True
        }
    }
    
    if not config_path or not os.path.exists(config_path):
        if logger:
            logger.warning(f"Config globale non trouvée ({config_path}), utilisation des valeurs par défaut")
        return default_config
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
        
        # Fusion profonde des configs
        config = merge_configs(default_config, user_config)
        
        if logger:
            logger.info(f"Config globale chargée depuis : {config_path}")
        
        return config
    
    except Exception as e:
        if logger:
            logger.error(f"Erreur lors du chargement de la config globale : {e}")
        return default_config


def merge_configs(default: dict, user: dict) -> dict:
    """Fusionne deux dictionnaires de configuration."""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result

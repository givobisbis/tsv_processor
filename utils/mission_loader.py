import yaml


def load_mission_config(config_path: str) -> dict:
    """Charge la configuration YAML d'une mission."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
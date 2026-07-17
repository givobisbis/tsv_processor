# ggggggg
# Bonjour depuis Qwen Coder
# Modifié depuis Qwen Coder
import os
import sys
from dotenv import load_dotenv
from utils.mission_loader import load_mission_config
from graph.builder import build_graph


def main():
    load_dotenv()

    if len(sys.argv) < 2:
        print("Usage: python main.py missions/<nom_mission>/config.yaml")
        sys.exit(1)

    config_path = sys.argv[1]
    config = load_mission_config(config_path)

    initial_state = {
        "input_file": config["input_file"],
        "output_file": config["output_file"],
        "model_key": config.get("model_key", "default"),
        "batch_size": config.get("batch_size", 10),
        "dataframe": None,
        "batches": [],
        "current_batch_index": 0,
        "results": [],
        "errors": [],
        "status": "pending",
        "mission_config": config,  # ← Correction : passe la config complète au graphe
    }

    graph = build_graph()
    result = graph.invoke(initial_state)

    print(f"\nStatut final : {result['status']}")
    if result["errors"]:
        print(f"Erreurs : {result['errors']}")


if __name__ == "__main__":
    main()
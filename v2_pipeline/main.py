#!/usr/bin/env python3
"""
Pipeline TSV Processor V2 - Version améliorée
==============================================
Cette version inclut :
- Logging structuré avec sauvegarde dans un fichier
- Validation des données d'entrée
- Gestion des erreurs avec retries automatiques
- Parsing robuste des réponses LLM
- Sauvegarde avec backup automatique
- Configuration centralisée
- Support des checkpoints (prêt pour extension)

Usage:
    python v2_pipeline/main.py missions/<nom_mission>/config.yaml [--config <config_globale.yaml>]
"""
import os
import sys
import argparse
from dotenv import load_dotenv

# Import des modules V2
from v2_pipeline.mission_loader import load_mission_config, load_global_config
from v2_pipeline.logger import setup_logger
from v2_pipeline.builder import build_graph


def parse_arguments():
    """Parse les arguments en ligne de commande."""
    parser = argparse.ArgumentParser(
        description="Pipeline TSV Processor V2 - Traitement de fichiers TSV avec LLM"
    )
    parser.add_argument(
        "mission_config",
        help="Chemin vers le fichier de config de la mission (ex: missions/ma_mission/config.yaml)"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Chemin vers la config globale optionnelle (ex: v2_pipeline/config.yaml)"
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Niveau de logging (override la config)"
    )
    return parser.parse_args()


def main():
    """Point d'entrée principal du pipeline V2."""
    args = parse_arguments()
    
    # Charger les variables d'environnement
    load_dotenv()
    
    # Charger la configuration globale
    global_config = load_global_config(args.config)
    
    # Déterminer le niveau de log
    log_level = args.log_level or global_config["general"]["log_level"]
    log_file = global_config["general"]["log_file"]
    
    # Initialiser le logger
    logger = setup_logger(
        name="tsv_processor_v2_main",
        log_level=log_level,
        log_file=log_file
    )
    
    logger.info("=" * 60)
    logger.info("Démarrage du Pipeline TSV Processor V2")
    logger.info("=" * 60)
    
    # Charger la configuration de la mission
    try:
        mission_config = load_mission_config(args.mission_config, logger)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Impossible de charger la config de mission : {e}")
        sys.exit(1)
    
    # Préparer l'état initial enrichi
    initial_state = {
        # Configuration de base
        "input_file": mission_config["input_file"],
        "output_file": mission_config["output_file"],
        "model_key": mission_config.get("model_key", "default"),
        "batch_size": mission_config.get("batch_size", global_config["batching"]["default_batch_size"]),
        
        # État du traitement
        "dataframe": None,
        "batches": [],
        "current_batch_index": 0,
        "results": [],
        "errors": [],
        "status": "pending",
        "mission_config": mission_config,
        
        # Métadonnées
        "checkpoint_data": None,
        "processed_count": 0,
        "failed_count": 0,
        
        # Configurations avancées
        "llm_config": global_config["llm"],
        "validation_config": global_config["validation"],
        "save_config": global_config["save"],
    }
    
    logger.info(f"Mission : {mission_config['mission_name']}")
    logger.info(f"Fichier d'entrée : {initial_state['input_file']}")
    logger.info(f"Fichier de sortie : {initial_state['output_file']}")
    logger.info(f"Modèle : {mission_config.get('model_name', 'default')}")
    logger.info(f"Taille des lots : {initial_state['batch_size']}")
    
    # Construire et exécuter le graphe
    try:
        graph = build_graph()
        result = graph.invoke(initial_state)
        
        # Rapport final
        logger.info("=" * 60)
        logger.info("TRAITEMENT TERMINÉ")
        logger.info(f"Statut final : {result['status']}")
        logger.info(f"Lots traités : {result['processed_count']}")
        logger.info(f"Erreurs : {result['failed_count']}")
        
        if result["errors"]:
            logger.warning(f"{len(result['errors'])} erreurs rencontrées :")
            for error in result["errors"]:
                logger.warning(f"  - {error}")
        
        if result["status"] == "completed":
            logger.info(f"Résultats sauvegardés dans : {result['output_file']}")
            logger.info("=" * 60)
            print(f"\n✅ Succès ! {result['processed_count']} lots traités.")
            print(f"📄 Résultats : {result['output_file']}")
        else:
            logger.error("Le pipeline a échoué ou été interrompu")
            print(f"\n❌ Échec ! Statut : {result['status']}")
            if result["errors"]:
                print(f"   Erreurs : {len(result['errors'])}")
        
        return 0 if result["status"] == "completed" else 1
    
    except Exception as e:
        logger.critical(f"Erreur critique du pipeline : {e}", exc_info=True)
        print(f"\n💥 Erreur critique : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

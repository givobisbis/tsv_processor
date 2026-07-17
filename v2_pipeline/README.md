# Pipeline TSV Processor - Version 2 (V2)

Cette version améliorée inclut toutes les fonctionnalités demandées tout en conservant l'architecture originale.

## 📁 Structure du dossier `v2_pipeline/`

```
v2_pipeline/
├── __init__.py          # Initialisation du package
├── config.yaml          # Configuration globale centralisée
├── main.py              # Point d'entrée principal
├── logger.py            # Logging structuré avec fichier
├── state.py             # État partagé enrichi
├── nodes.py             # Nœuds du graphe améliorés
├── builder.py           # Constructeur du graphe
├── batcher.py           # Gestion des lots avec validation
├── tsv_handler.py       # Lecture/écriture TSV robuste
└── mission_loader.py    # Chargement de config avec validation
```

## 🚀 Améliorations apportées

### 1. **Logging complet**
- Logs structurés avec timestamps
- Sortie console + fichier (`logs/pipeline_v2.log`)
- Niveaux de log configurables (DEBUG, INFO, WARNING, ERROR)
- Traces détaillées à chaque étape du pipeline

### 2. **Gestion des erreurs avec Retries**
- Retry automatique sur les appels LLM (3 tentatives)
- Délai entre les retries (2 secondes)
- Continuité du traitement même en cas d'erreur sur un lot
- Comptage des succès et échecs

### 3. **Validation des données**
- Vérification des colonnes requises avant traitement
- Détection et gestion des lignes vides
- Validation de la configuration YAML
- Messages d'erreur explicites

### 4. **Parsing robuste des réponses LLM**
- Multiples patterns de recherche pour extraire les données
- Support des variations de format (`:`, `:`, `=`)
- Nettoyage automatique des chaînes
- Fallback gracieux en cas de parsing partiel

### 5. **Sauvegarde sécurisée**
- Backup automatique du fichier de sortie existant
- Création des dossiers manquants
- Sauvegarde intermédiaire configurable

### 6. **Configuration centralisée**
- Fichier `config.yaml` unique pour tous les paramètres
- Fusion avec les valeurs par défaut
- Override possible via arguments CLI

### 7. **Support des checkpoints (prêt)**
- État sérialisable pour sauvegarde
- Métadonnées de progression
- Architecture prête pour reprise sur erreur

## 📖 Utilisation

### Commande de base
```bash
python v2_pipeline/main.py missions/exemple_mission/config.yaml
```

### Avec configuration globale
```bash
python v2_pipeline/main.py missions/exemple_mission/config.yaml --config v2_pipeline/config.yaml
```

### Avec niveau de log personnalisé
```bash
python v2_pipeline/main.py missions/exemple_mission/config.yaml --log-level DEBUG
```

## 🔧 Configuration

### Fichier `v2_pipeline/config.yaml`

```yaml
general:
  log_level: INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
  log_file: logs/pipeline_v2.log
  enable_checkpointing: false
  checkpoint_dir: checkpoints/

llm:
  default_provider: requesty
  api_base: https://router.requesty.ai/v1
  temperature: 0.2
  max_tokens: 4000
  timeout: 60                  # secondes
  max_retries: 3               # nombre de tentatives
  retry_delay: 2               # secondes entre retries

batching:
  default_batch_size: 10
  max_concurrent_batches: 1

validation:
  check_required_columns: true
  skip_invalid_rows: false
  max_empty_rows: 10

save:
  auto_save_interval: 5        # sauvegarder tous les X lots
  backup_enabled: true
```

### Variables d'environnement requises

Créer un fichier `.env` à la racine :
```
REQUESTY_API_KEY=ghp_votre_token_ici
```

## 📊 Comparaison V1 vs V2

| Fonctionnalité | V1 | V2 |
|---------------|----|----|
| Logging basique | ✅ | ✅✅ (fichier + niveaux) |
| Gestion erreurs | ⚠️ Partielle | ✅✅ Complète avec retries |
| Validation données | ❌ | ✅✅ Colonnes + lignes vides |
| Parsing LLM | ⚠️ Simple | ✅✅ Multi-patterns robuste |
| Backup sauvegarde | ❌ | ✅ Automatique |
| Config centralisée | ❌ | ✅ Unique fichier |
| Checkpoints | ❌ | 🔄 Prêt (architecture) |
| Arguments CLI | ⚠️ Basiques | ✅✅ Avancés avec help |

## 🎯 Exécution parallèle des deux versions

Les deux systèmes sont totalement indépendants :

```bash
# Version 1 (originale)
python main.py missions/exemple_mission/config.yaml

# Version 2 (améliorée)
python v2_pipeline/main.py missions/exemple_mission/config.yaml
```

## 📝 Notes importantes

1. **Compatibilité** : La V2 utilise les mêmes fichiers de mission que la V1
2. **Sécurité** : La V2 ne modifie jamais les fichiers de la V1
3. **Logs** : Les logs V2 sont dans `logs/pipeline_v2.log`
4. **Backups** : Les anciens résultats sont sauvegardés avec `.bak`

## 🐛 Dépannage

### Le pipeline ne démarre pas
- Vérifier que `REQUESTY_API_KEY` est défini dans `.env`
- Vérifier que le fichier de config de mission existe
- Consulter les logs dans `logs/pipeline_v2.log`

### Erreurs de parsing
- Activer le mode DEBUG : `--log-level DEBUG`
- Vérifier le format des réponses du LLM
- Examiner le fichier `prompt.txt` de la mission

### Problèmes de performances
- Ajuster `batch_size` dans la config
- Modifier `max_retries` et `timeout` si nécessaire

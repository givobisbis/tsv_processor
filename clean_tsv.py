import pandas as pd

# 1. Lire le fichier actuel en supposant qu'il est mal formatté mais lisible
# On essaie de lire les deux colonnes attendues
try:
    # On force la lecture en prenant tout le contenu comme une seule colonne pour le réparer
    with open("data/argos_eval.tsv", "r", encoding="utf-8") as f:
        lines = f.readlines()

    clean_lines = []
    for line in lines:
        # On enlève les espaces superflus et on s'assure qu'il n'y a pas de retour chariot bizarre
        clean_line = line.strip()
        if clean_line:
            clean_lines.append(clean_line)

    # 2. Recréer un vrai TSV propre
    # On suppose que la première ligne est l'en-tête et les suivantes les données
    # Si le fichier original avait des sauts de ligne au milieu des cellules JSON, c'est plus complexe.
    # Pour l'instant, on va utiliser Pandas pour lire ce qu'on peut et réécrire proprement.
    
    # Méthode radicale : on lit le fichier tel quel et on le réécrit avec des vraies tabulations
    df = pd.read_csv("data/argos_eval.tsv", sep="\t", header=0, engine='python', on_bad_lines='skip')
    
    # On ne garde que les deux colonnes qui nous intéressent
    if 'model_input' in df.columns and 'cleaned_model_response' in df.columns:
        df_clean = df[['model_input', 'cleaned_model_response']]
        df_clean.to_csv("data/argos_eval_clean.tsv", sep="\t", index=False, encoding="utf-8")
        print("✅ Fichier nettoyé créé : data/argos_eval_clean.tsv")
    else:
        print("❌ Erreur : Les colonnes 'model_input' ou 'cleaned_model_response' sont introuvables.")

except Exception as e:
    print(f"❌ Erreur lors du nettoyage : {e}")
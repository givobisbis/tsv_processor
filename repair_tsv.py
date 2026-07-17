import pandas as pd

input_file = "data/argos_eval.tsv"
output_file = "data/argos_eval_repaired.tsv"

try:
    # On lit le fichier en traitant chaque ligne comme une chaîne brute
    # sep=None permet à Pandas de deviner le séparateur, mais on force \t ici
    # on_bad_lines='warn' permet de continuer même si une ligne est bizarre
    df = pd.read_csv(
        input_file, 
        sep="\t", 
        header=0, 
        names=["model_input", "cleaned_model_response"], # On force les noms
        engine="python", 
        on_bad_lines="skip"
    )

    # On nettoie les éventuels espaces autour des valeurs
    df['model_input'] = df['model_input'].astype(str).str.strip()
    df['cleaned_model_response'] = df['cleaned_model_response'].astype(str).str.strip()

    # On sauvegarde proprement
    df.to_csv(output_file, sep="\t", index=False, encoding="utf-8")
    
    print(f"✅ Fichier réparé créé : {output_file}")
    print(f"📊 Nombre de lignes trouvées : {len(df)}")

except Exception as e:
    print(f"❌ Erreur lors de la réparation : {e}")
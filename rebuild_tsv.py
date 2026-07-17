import json

input_file = "data/argos_eval.tsv"
output_file = "data/argos_final.tsv"

def rebuild_tsv():
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # On sépare tout par les retours à la ligne
    raw_lines = content.split('\n')
    
    final_rows = []
    current_input = ""
    current_response = ""
    in_json = False
    
    # On saute la première ligne si c'est l'en-tête
    start_idx = 0
    if raw_lines and raw_lines[0].startswith("model_input"):
        start_idx = 1

    for line in raw_lines[start_idx:]:
        line = line.strip()
        if not line: continue

        # Détection d'une nouvelle ligne de données : commence par { ou "
        if line.startswith("{") or line.startswith('"'):
            # Si on avait déjà une ligne en cours, on la sauvegarde
            if current_input and current_response:
                final_rows.append((current_input, current_response))
            
            # On démarre une nouvelle paire
            # On cherche la tabulation qui sépare input de response
            if "\t" in line:
                parts = line.split("\t", 1)
                current_input = parts[0]
                current_response = parts[1] if len(parts) > 1 else ""
            else:
                current_input = line
                current_response = ""
            in_json = True
        else:
            # C'est la suite d'une ligne précédente (saut de ligne dans le JSON ou le texte)
            if in_json:
                if current_response: 
                    current_response += " " + line
                else:
                    current_input += " " + line

    # Ne pas oublier la dernière ligne
    if current_input and current_response:
        final_rows.append((current_input, current_response))

    # Écriture propre
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("model_input\tcleaned_model_response\n") # En-tête
        for inp, resp in final_rows:
            # On nettoie les tabulations internes qui pourraient casser le TSV
            clean_inp = inp.replace("\t", " ")
            clean_resp = resp.replace("\t", " ")
            f.write(f"{clean_inp}\t{clean_resp}\n")

    print(f"✅ Fichier reconstruit : {output_file}")
    print(f"📊 Lignes trouvées : {len(final_rows)}")

try:
    rebuild_tsv()
except Exception as e:
    print(f"❌ Erreur : {e}")
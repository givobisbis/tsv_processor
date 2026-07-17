import re

input_file = "data/argos_eval.tsv"
output_file = "data/argos_eval_fixed.tsv"

try:
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    # On sépare les lignes en gardant uniquement celles qui commencent par un '{' ou l'en-tête
    lines = content.split('\n')
    
    clean_lines = []
    current_line = ""
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Si la ligne commence par une accolade ou est l'en-tête, c'est une nouvelle entrée
        if line.startswith("{") or line.startswith("model_input"):
            if current_line:
                clean_lines.append(current_line)
            current_line = line
        else:
            # Sinon, c'est la suite de la ligne précédente (saut de ligne dans le JSON)
            current_line += " " + line
            
    if current_line:
        clean_lines.append(current_line)

    # Écriture du fichier corrigé
    with open(output_file, "w", encoding="utf-8") as f:
        for line in clean_lines:
            f.write(line + "\n")

    print(f"✅ Fichier corrigé créé : {output_file}")
    print(f"📊 Nombre de lignes traitées : {len(clean_lines)}")

except Exception as e:
    print(f"❌ Erreur : {e}")
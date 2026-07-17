import re

input_file = "data/argos_eval.tsv"
output_file = "data/argos_ready.tsv"

def fix_tsv():
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    cleaned_rows = []
    current_row_parts = []
    
    for line in lines:
        # On enlève les sauts de ligne et espaces inutiles aux extrémités
        stripped = line.strip()
        if not stripped: continue
        
        # Si c'est l'en-tête, on l'ignore ou on le garde pour vérification
        if stripped.startswith("model_input"):
            continue
            
        # On ajoute le morceau de ligne au courant
        current_row_parts.append(stripped)
        
        # Astuce : si la ligne se termine par un point ou une parenthèse fermante 
        # et qu'on a déjà du contenu, on considère que c'est la fin de la réponse
        # Mais le plus sûr est de compter les accolades JSON pour l'input
        
        # Méthode simple : on cherche la première tabulation dans la ligne originale
        # Si la ligne originale contient une tabulation, c'est le début d'une nouvelle entrée
        if "\t" in line:
            # C'est une nouvelle ligne complète ou le début d'une nouvelle
            full_line = "".join(current_row_parts)
            parts = full_line.split("\t", 1)
            if len(parts) == 2:
                cleaned_rows.append((parts[0], parts[1]))
            current_row_parts = [] # On reset pour la prochaine

    # Gestion de la dernière ligne si elle n'a pas été traitée
    if current_row_parts:
        full_line = "".join(current_row_parts)
        if "\t" in full_line:
            parts = full_line.split("\t", 1)
            cleaned_rows.append((parts[0], parts[1]))

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("model_input\tcleaned_model_response\n")
        for inp, resp in cleaned_rows:
            # On remplace les tabulations internes par des espaces pour ne pas casser le TSV
            f.write(f"{inp.replace(chr(9), ' ')}\t{resp.replace(chr(9), ' ')}\n")

    print(f"✅ Fichier prêt : {output_file}")
    print(f"📊 Lignes : {len(cleaned_rows)}")

try:
    fix_tsv()
except Exception as e:
    print(f"❌ Erreur : {e}")
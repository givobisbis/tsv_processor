import pandas as pd


def read_tsv(filepath: str) -> pd.DataFrame:
    """Lit un fichier TSV et retourne un DataFrame."""
    return pd.read_csv(filepath, sep="\t", dtype=str)


def write_tsv(data: list[dict], filepath: str) -> None:
    """Écrit une liste de dictionnaires dans un fichier TSV."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, sep="\t", index=False)
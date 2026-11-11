"""Baixa somente as imagens declaradas no manifesto, verificando SHA-256."""
import argparse
import hashlib
import io
from pathlib import Path
import pandas as pd
import requests
from PIL import Image
from pipeline import config


def collect(manifest):
    table = pd.read_csv(manifest).fillna("")
    for row in table.to_dict("records"):
        path = (config.ROOT_DIR / row["local_path"]).resolve()
        if not path.is_relative_to(config.DATA_DIR.resolve()):
            raise ValueError("Destino deve estar dentro de data/.")
        # Este coletor aceita apenas a origem pública fixa do manifesto fornecido.
        prefix = "https://huggingface.co/datasets/shivank21/mmconflict-restaurant-menus-500/resolve/main/train/images/"
        if not row["source_url"].startswith(prefix):
            raise ValueError("Fonte não reconhecida. Adicione outras imagens manualmente com sua atribuição.")
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"]:
            continue
        response = requests.get(row["source_url"], timeout=60)
        response.raise_for_status()
        data = response.content
        if len(data) > 20 * 1024 * 1024:
            raise ValueError("Imagem maior que 20 MB.")
        with Image.open(io.BytesIO(data)) as image:
            image.verify()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise ValueError(f"Hash divergente: {path.name}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"Baixado e verificado: {path.name}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path, nargs="?", default=config.DATA_DIR / "manifest.csv")
    collect(p.parse_args().manifest)

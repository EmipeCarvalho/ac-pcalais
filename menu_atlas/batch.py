"""python -m menu_atlas.batch data/manifest.csv --db data/evaluation.sqlite"""
import argparse
import json
from pathlib import Path
import pandas as pd
from prefect import flow
from .pipeline import process_menu
from .storage import tables, summarize

@flow(name="Menu Atlas • Avaliação em lote", persist_result=False)
def run_batch(manifest: str, db: str):
    frame=pd.read_csv(manifest).fillna("")
    if not {"source_url","local_path"}.issubset(frame.columns):
        raise ValueError("Manifesto exige source_url e local_path.")
    # Usa somente imagens locais, previamente baixadas e verificadas.
    hashes=set()
    import hashlib
    results=[]
    for row in frame.to_dict("records"):
        data=Path(row["local_path"]).read_bytes()
        digest=hashlib.sha256(data).hexdigest()
        if digest in hashes:
            continue
        hashes.add(digest)
        results.append(process_menu(data,source=row["source_url"],db_path=db))
    runs,_=tables(db)
    runs=runs[runs.id.isin([r["id"] for r in results])]
    metrics=summarize(runs)
    metrics["distinct_images"]=len(hashes)
    metrics["minimum_50_met"]=len(hashes)>=50 and metrics["processed"]>=50
    output=Path("reports"); output.mkdir(exist_ok=True)
    (output/"metrics.json").write_text(json.dumps(metrics,indent=2,ensure_ascii=False,allow_nan=False))
    runs.to_csv(output/"runs.csv",index=False)
    (output/"report.md").write_text("# Relatório de avaliação — Menu Atlas\n\n"+
        "Resultados reais desta execução, antes de filtrar itens inválidos.\n\n"+
        "| Indicador | Resultado |\n|---|---|\n"+
        "\n".join(f"| {k} | {v if v is not None else 'Não disponível'} |" for k,v in metrics.items())+
        "\n\n## Análise qualitativa\nInspecione os itens sinalizados e compare com as imagens. Documente exemplos de falhas de layout, ruído e alucinação. Plausibilidade não equivale a acurácia.\n")
    return metrics

if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--db",default="data/evaluation.sqlite")
    args=parser.parse_args()
    print(json.dumps(run_batch(args.manifest,args.db),indent=2))

"""Lote reproduzível com manifesto, SHA-256 e relatório de resultados reais."""
import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from pipeline import config, storage
from pipeline.flow import menu_pipeline
from pipeline.metrics import compute_metrics

EXTS = {".jpg", ".jpeg", ".png", ".webp"}


def select_files(manifest=None):
    if manifest:
        table = pd.read_csv(manifest).fillna("")
        if not {"source_url", "local_path"}.issubset(table.columns):
            raise ValueError("Manifesto exige source_url e local_path.")
        files = []
        for row in table.to_dict("records"):
            path = (config.ROOT_DIR / row["local_path"]).resolve()
            if not path.is_relative_to(config.DATA_DIR.resolve()):
                raise ValueError("As imagens precisam estar dentro de data/.")
            if row.get("sha256") and hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"Hash divergente: {path.name}")
            files.append(path)
        return files
    return sorted(p for p in config.DATA_DIR.glob("*") if p.suffix.lower() in EXTS)


def run_batch(force=False, manifest=None, delay=0):
    files = select_files(manifest)
    runs = storage.read_runs()
    done = set(runs.loc[runs.status != "erro", "image_sha256"].dropna()) if "image_sha256" in runs else set()
    seen = set()
    todo = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen or (not force and digest in done):
            continue
        seen.add(digest)
        todo.append(path)
    print(f"{len(files)} imagens, {len(todo)} imagens distintas a processar")
    for i, path in enumerate(todo):
        if i and delay:
            time.sleep(delay)
        try:
            result = menu_pipeline(path.read_bytes(), path.name)["run"]
            print(f"{i + 1}/{len(todo)} {path.name}: {result['status']}, {result['n_items']} itens, custo={result['cost_usd']}")
        except Exception as exc:
            print(f"{i + 1}/{len(todo)} {path.name}: erro ({type(exc).__name__})")


def write_report():
    metrics = compute_metrics()
    runs = storage.read_runs()
    (config.REPORTS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    def fmt(value):
        return "Não disponível" if value is None else str(value)
    lines = ["# Relatório de qualidade", f"Gerado em {datetime.now(timezone.utc).isoformat()}", "",
             "Resultados reais dos CSVs atuais. A contagem de imagens distintas considera somente hashes registrados.",
             "Execuções antigas sem hash não comprovam a meta de 50 imagens distintas.", "",
             "| Indicador | Valor |", "|---|---|"]
    lines.extend(f"| {key} | {fmt(value)} |" for key, value in metrics.items() if not isinstance(value, dict))
    lines.extend(["", "## Configuração e interpretação",
                  f"Modelos presentes nos registros: {', '.join(sorted(runs.model.dropna().astype(str).unique())) if len(runs) else 'nenhum'}.",
                  "Missing: categoria, nome e preço. Preços razoáveis: todos os itens no denominador, incluindo preços ausentes.",
                  "Custos desconhecidos não são zero. O custo conhecido é um subtotal, não o total faturado quando existem falhas sem uso reportado.",
                  "A latência das novas execuções inclui o append dos dois CSVs, sem a atualização posterior da própria medição.",
                  "Execuções antigas mantêm a latência e decisão de validação originais. Não reinterpretar esses registros como testes da versão corrigida.",
                  "", "## Evidências qualitativas",
                  "A análise está em docs/AVALIACAO.md. Para o lote final, registrar exemplos reais de layouts, ruído e erros de transcrição."])
    (config.REPORTS_DIR / "quality_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False, allow_nan=False))
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--delay", type=float, default=0, help="Intervalo entre imagens, em segundos")
    args = parser.parse_args()
    if args.delay < 0:
        parser.error("--delay precisa ser não negativo")
    if not args.report_only:
        run_batch(args.force, args.manifest, args.delay)
    write_report()

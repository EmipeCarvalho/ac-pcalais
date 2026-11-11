"""Métricas sobre dados brutos, sem mascarar preços ausentes ou custos desconhecidos."""
import pandas as pd
from . import config, storage


def _pct(num, den):
    return round(100 * num / den, 2) if den else None


def compute_metrics(items=None, runs=None):
    items = storage.read_items() if items is None else items
    runs = storage.read_runs() if runs is None else runs
    required = ["category", "item_name", "price"]
    n = len(items)
    missing = int(items[required].isna().sum().sum()) if n else 0
    prices = pd.to_numeric(items["price"], errors="coerce") if n else pd.Series(dtype=float)
    reasonable = prices.between(config.PRICE_MIN, config.PRICE_MAX)
    ok = runs[runs["status"] != "erro"] if len(runs) else runs
    def statistic(column, method="mean"):
        values = pd.to_numeric(ok[column], errors="coerce").dropna() if len(ok) else pd.Series(dtype=float)
        return round(float(getattr(values, method)()), 4) if len(values) else None
    def mean(column):
        values = pd.to_numeric(ok[column], errors="coerce").dropna() if len(ok) else pd.Series(dtype=float)
        return round(float(values.mean()), 4) if len(values) else None
    costs = pd.to_numeric(runs["cost_usd"], errors="coerce") if len(runs) else pd.Series(dtype=float)
    known = costs.notna()
    hashes = runs.get("image_sha256", pd.Series(dtype=str)).dropna()
    good_hashes = ok.get("image_sha256", pd.Series(dtype=str)).dropna()
    return {
        "menus_processados": len(runs),
        "menus_distintos_verificados": int(hashes.nunique()),
        "menus_distintos_sem_erro": int(good_hashes.nunique()),
        "meta_50_cardapios_atingida": good_hashes.nunique() >= 50,
        "menus_com_erro": int((runs["status"] == "erro").sum()) if len(runs) else 0,
        "menus_aprovados": int((runs["status"] == "aprovado").sum()) if len(runs) else 0,
        "menus_revisao_humana": int((runs["status"] == "revisao_humana").sum()) if len(runs) else 0,
        "itens_extraidos": n,
        "pct_missing_data": _pct(missing, n * len(required)),
        "pct_missing_por_campo": {c: _pct(int(items[c].isna().sum()), n) for c in required} if n else {},
        "pct_linhas_com_campo_faltante": _pct(int(items[required].isna().any(axis=1).sum()), n) if n else None,
        "pct_precos_razoaveis": _pct(int(reasonable.sum()), n),
        "precos_ausentes": int(prices.isna().sum()),
        "precos_fora_da_faixa": int((prices.notna() & ~reasonable).sum()),
        "faixa_preco_razoavel": [config.PRICE_MIN, config.PRICE_MAX],
        "latencia_media_s": mean("latency_s"),
        "latencia_p50_s": statistic("latency_s", "median"),
        "latencia_max_s": statistic("latency_s", "max"),
        "tokens_input_medio": mean("input_tokens"),
        "tokens_output_medio": mean("output_tokens"),
        "custo_medio_usd": round(float(costs.mean()), 6) if len(costs) and known.all() else None,
        "custo_total_usd": round(float(costs.sum()), 6) if len(costs) and known.all() else None,
        "custo_conhecido_usd": round(float(costs[known].sum()), 6),
        "execucoes_custo_desconhecido": int((~known).sum()),
        "score_gx_medio": mean("gx_score"),
    }

"""Interface Streamlit: foto do cardápio -> flow do Prefect -> cardápio transcrito e verificado.

Rodar (a partir de backend/):  .venv\\Scripts\\python -m streamlit run app.py
"""
import html
import time

import pandas as pd
import streamlit as st

from pipeline import config, flow, storage
from pipeline.metrics import compute_metrics
from pipeline.validation import CRITERIOS

st.set_page_config(page_title="Cardápios", page_icon="🍽️", layout="wide")

# ------------------------------------------------------------------ estilo
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;650;700;800&display=swap');
.stApp{--papel:light-dark(#FFFFFF,#192D27);--azulejo:light-dark(#22624E,#BADE93);--tinta:light-dark(#183B30,#E9F0E7);--suave:light-dark(#687E71,#A8BCAE);--rejunte:light-dark(#DFE8DD,#345043);--pontos:light-dark(#B5C9B4,#65816D);--ok:light-dark(#246D4D,#A9D988);--rev:light-dark(#9A6514,#E0B061);--erro:light-dark(#B23A2E,#F08A7E);--alerta:light-dark(#FBEDEB,#3A2427)}
html,body,.stApp,input,button,textarea,[data-testid="stMarkdownContainer"],h1,h2,h3,h4,h5{font-family:'Inter',sans-serif!important}
[data-testid="stHeader"]{background:transparent}.block-container{padding:2rem 2.8rem 4rem;max-width:1320px}h1,h2,h3,h4{letter-spacing:-.045em;font-weight:650!important}h3{font-size:1.45rem!important}button{transition:background .15s,border-color .15s}
.brandbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:25px}.brandname{display:flex;align-items:center;gap:11px;font-size:21px;letter-spacing:-.8px;font-weight:700;color:var(--tinta)}.brandmark{display:grid;place-items:center;width:36px;height:36px;border-radius:11px;background:#1C4B3A;color:#D5EBAB;font-size:25px}.brandmeta{font-size:10px;text-transform:uppercase;letter-spacing:.14em;color:var(--suave);display:flex;align-items:center;gap:8px}.brandmeta::before{content:'';width:6px;height:6px;border-radius:50%;background:#80A86F}
.hero{background:#153E31;border:1px solid #285441;border-radius:25px;padding:34px 40px;display:flex;align-items:center;justify-content:space-between;gap:35px;margin-bottom:25px;position:relative;overflow:hidden}.hero::after{content:'';position:absolute;width:300px;height:300px;right:-100px;top:-130px;border:1px solid #406A49;border-radius:50%;box-shadow:0 0 0 35px #214B361f,0 0 0 70px #43653e15;pointer-events:none}.hero-copy{position:relative;z-index:1}.eyebrow{color:#B1CE98;font-size:10px;letter-spacing:.18em;font-weight:600;margin-bottom:16px}.hero h1{font-size:38px;line-height:1.13;color:#F5F8ED;margin:0;padding:0;font-weight:600!important;letter-spacing:-1.7px}.hero p{font-size:13px;line-height:1.8;color:#B7CDBC;margin:15px 0 0;max-width:500px}.hero-aside{position:relative;z-index:1;border-left:1px solid #3B5E48;padding-left:30px;min-width:210px;color:#BED1B5;font-size:12px;line-height:2.1}.hero-aside strong{display:block;color:#D7ECB0;font-size:30px;font-weight:500;letter-spacing:-1.4px;line-height:1.2;margin-bottom:10px}.hero-aside span{display:block;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#90AF8C;margin-top:6px}
[data-baseweb="tab-list"]{gap:6px;background:light-dark(#E7EEE3,#15271F);border:1px solid var(--rejunte);border-radius:13px;padding:5px;margin-bottom:23px;min-height:49px;width:fit-content;max-width:100%}[data-baseweb="tab"]{border-radius:9px;padding:10px 22px;height:auto;color:var(--suave)}[data-baseweb="tab"] p{font-size:12px;font-weight:600}[data-baseweb="tab"][aria-selected="true"]{background:var(--papel);color:var(--tinta);box-shadow:0 2px 5px #16371b0c}[data-baseweb="tab-highlight"],[data-baseweb="tab-border"]{display:none}
[data-testid="stFileUploader"]{background:var(--papel);padding:25px;border:1px solid var(--rejunte);border-radius:22px;box-shadow:0 8px 25px #173b2103}[data-testid="stFileUploader"] label p{font-weight:600;font-size:14px;color:var(--tinta)}[data-testid="stFileUploaderDropzone"]{background:light-dark(#F8FAF5,#14261D);border:1.5px dashed var(--pontos);border-radius:15px;padding:40px 24px;min-height:165px;margin-top:14px}[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--azulejo)}
.stButton button,.stDownloadButton button{border-radius:11px!important;padding:.65rem 1.1rem;font-weight:600;font-size:12px;border-color:var(--rejunte);min-height:43px}.stButton button[kind="primary"]{background:#20583F;color:white;border:1px solid #20583F}.stButton button[kind="primary"]:hover{background:#153E31;border-color:#153E31}.stDownloadButton button{color:var(--azulejo);background:var(--papel)}
[data-testid="stMetric"]{background:var(--papel);border:1px solid var(--rejunte);border-radius:19px;padding:22px 24px;margin:7px 0 15px;box-shadow:0 5px 18px #16371b03}[data-testid="stMetricLabel"] p{color:var(--suave);font-size:11px;font-weight:500}[data-testid="stMetricValue"]{font-variant-numeric:tabular-nums;letter-spacing:-.055em;font-size:31px;font-weight:600;color:var(--tinta)}[data-testid="stDataFrame"]{border:1px solid var(--rejunte);border-radius:17px;overflow:hidden}[data-testid="stImage"] img{border-radius:17px}[data-testid="stExpander"]{border-radius:15px}
.steps{display:grid;grid-template-columns:repeat(3,1fr);gap:13px;margin:25px 0 10px}.step{border:1px solid var(--rejunte);border-radius:17px;padding:20px 22px;background:var(--papel)}.step small{color:#699060;font-size:10px;font-weight:600;letter-spacing:.12em}.step strong{display:block;color:var(--tinta);font-size:13px;letter-spacing:-.3px;margin:12px 0 6px}.step p{font-size:11px;color:var(--suave);margin:0;line-height:1.7}.workspace-footer{display:flex;justify-content:space-between;font-size:10px;color:var(--suave);border-top:1px solid var(--rejunte);margin-top:45px;padding-top:18px;letter-spacing:.03em}
.veredito{border:1px solid var(--rejunte);border-left:4px solid;padding:18px 21px;background:var(--papel);border-radius:15px;margin-bottom:18px}.veredito strong{display:block;font-size:16px;font-weight:600;letter-spacing:-.4px;margin-bottom:5px}.veredito span{color:var(--suave);font-size:12px}.veredito ul{margin:7px 0 0;padding-left:18px;color:var(--tinta);font-size:12px}.veredito.aprovado{border-left-color:var(--ok)}.veredito.aprovado strong{color:var(--ok)}.veredito.revisao_humana{border-left-color:var(--rev)}.veredito.revisao_humana strong{color:var(--rev)}.fatos{display:flex;flex-wrap:wrap;gap:10px 20px;color:var(--suave);font-size:12px;margin:0 0 20px}.fatos b{color:var(--tinta);font-weight:600;font-variant-numeric:tabular-nums}
.cardapio{background:var(--papel);border:1px solid var(--rejunte);border-radius:23px;padding:30px;box-shadow:0 10px 30px #16371b05}.cardapio .rest{font-size:25px;font-weight:650;color:var(--tinta);letter-spacing:-1px;margin:0 0 7px}.cardapio .obs{color:var(--suave);font-size:12px;margin:0 0 24px}.cardapio h4{font-size:13px;font-weight:700!important;color:var(--azulejo);margin:25px 0 9px;padding-bottom:10px;border-bottom:1px solid var(--rejunte);letter-spacing:.01em}.cardapio h4:first-of-type{margin-top:20px}.prato{padding:12px 0}.prato .linha{display:flex;align-items:baseline;gap:8px}.prato .nome{font-size:13px;font-weight:600;color:var(--tinta)}.prato .var{color:var(--suave);font-size:11px}.prato .pontos{flex:1;min-width:15px}.prato .preco{font-size:13px;font-weight:650;color:var(--azulejo);font-variant-numeric:tabular-nums;white-space:nowrap}.prato .preco.vazio{color:var(--erro)}.prato .desc{color:var(--suave);font-size:12px;line-height:1.6;margin-top:5px;max-width:62ch}.prato .attr{font-size:10px;color:var(--azulejo);margin-top:5px}.prato.alerta{background:var(--alerta);margin:3px -10px;padding:12px 10px;border-radius:10px}.prato .motivo{font-size:11px;color:var(--erro);margin-top:7px}.grupo{background:var(--papel);border:1px solid var(--rejunte);border-radius:16px;padding:20px;margin-bottom:13px}.grupo h5{font-size:13px;font-weight:600;margin:0 0 12px;color:var(--tinta)}.regra{display:flex;gap:10px;padding:5px 0;font-size:12px}.regra .ic{width:15px;flex-shrink:0;font-weight:700}.regra.ok .ic{color:var(--ok)}.regra.falha,.regra.falha .ic{color:var(--erro)}.regra small{color:var(--suave)}
@media(max-width:760px){.block-container{padding:1.3rem 1.2rem 3rem}.brandmeta{font-size:8px}.hero{padding:28px 25px;border-radius:20px}.hero h1{font-size:32px}.hero-aside{display:none}.steps{grid-template-columns:1fr;gap:8px}.step{padding:15px 18px}.step small{float:left;margin:5px 13px 20px 0}.step strong{margin:0 0 5px}[data-baseweb="tab"]{padding:10px 15px}[data-testid="stFileUploader"]{padding:18px}[data-testid="stMetric"]{padding:17px 20px}[data-testid="stImage"] img{max-height:280px;object-fit:contain}.cardapio{padding:22px}.workspace-footer{font-size:8px;gap:20px}}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
""",
    unsafe_allow_html=True,
)

STATUS_TXT = {"aprovado": "Aprovado", "revisao_humana": "Precisa de revisão", "erro": "Erro"}
FLAGS = {
    "flag_missing_required": "campo faltando",
    "flag_price_unreasonable": "preço fora da faixa",
    "flag_price_outlier": "preço destoa da categoria",
    "flag_duplicate": "item repetido",
    "flag_item_equals_category": "parece cabeçalho, não item",
    "flag_variant_order": "tamanhos com preço fora de ordem",
}
STEPS = [
    ("preprocess", "Preparando a imagem"),
    ("extract", f"Lendo o cardápio com {config.OPENAI_MODEL}"),
    ("structure", "Organizando itens e preços"),
    ("validate", "Conferindo com os guardrails"),
    ("persist", "Salvando no CSV"),
]
e = html.escape


def money(v, cur="BRL") -> str:
    if v is None or pd.isna(v):
        return "sem preço"
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return {"BRL": "R$ ", "USD": "US$ ", "EUR": "€ "}.get(cur, f"{cur} ") + s


def br(v, nd=1) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"{v:.{nd}f}".replace(".", ",")


def item_flags(it: dict) -> list[str]:
    return [txt for col, txt in FLAGS.items() if it.get(col) in (True, "True")]


def render_menu(items: pd.DataFrame, restaurant: str | None, notes: str | None) -> None:
    """Desenha o cardápio transcrito como um cardápio impresso."""
    if items.empty:
        st.info("Nenhum item foi extraído desta imagem. Confira se a foto mostra um cardápio e se está legível.")
        return
    parts = ['<div class="cardapio">']
    if restaurant:
        parts.append(f'<p class="rest">{e(restaurant)}</p>')
    if notes:
        parts.append(f'<p class="obs">{e(notes)}</p>')
    for cat, rows in items.groupby("category", sort=False, dropna=False):
        parts.append(f"<h4>{e(str(cat) if pd.notna(cat) else 'Sem categoria')}</h4>")
        for (_, name), grp in rows.groupby([rows["category"], rows["item_name"]], sort=False, dropna=False):
            first = grp.iloc[0].to_dict()
            for _, row in grp.iterrows():
                it = row.to_dict()
                flags = item_flags(it)
                var = f' <span class="var">{e(str(it["variant_label"]))}</span>' if pd.notna(it.get("variant_label")) else ""
                is_first = row.name == grp.index[0]
                price_cls = "preco" if pd.notna(it.get("price")) else "preco vazio"
                block = [f'<div class="prato{" alerta" if flags else ""}">',
                         f'<div class="linha"><span class="nome">{e(str(name) if pd.notna(name) else "(sem nome)")}</span>{var}'
                         f'<span class="pontos"></span><span class="{price_cls}">{money(it.get("price"), it.get("currency"))}</span></div>']
                if is_first and pd.notna(first.get("description")):
                    block.append(f'<div class="desc">{e(str(first["description"]))}</div>')
                if is_first and pd.notna(first.get("attributes")):
                    block.append(f'<div class="attr">{e(str(first["attributes"]).replace("; ", ", "))}</div>')
                if flags:
                    block.append(f'<div class="motivo">{e(", ".join(flags)).capitalize()}</div>')
                block.append("</div>")
                parts.append("".join(block))
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_checks(validation: dict) -> None:
    out = []
    for crit in CRITERIOS:
        regras = [c for c in validation["checks"] if c.get("criterio") == crit]
        if not regras:
            continue
        out.append(f'<div class="grupo"><h5>{e(crit)}</h5>')
        for c in regras:
            extra = ""
            if not c["success"] and c.get("unexpected_count"):
                extra = f' <small>({c["unexpected_count"]} linha{"s" if c["unexpected_count"] > 1 else ""})</small>'
            out.append(f'<div class="regra {"ok" if c["success"] else "falha"}"><span class="ic">{"✓" if c["success"] else "✕"}</span>'
                       f'<span>{e(c["check"])}{extra}</span></div>')
        out.append("</div>")
    st.markdown("".join(out), unsafe_allow_html=True)
    st.caption(
        f"Aprovado quando pelo menos {int(config.REVIEW_THRESHOLD * 100)}% das verificações passam "
        "e todas as regras essenciais de preço, campos obrigatórios, texto e duplicidade passam. "
        "Abaixo disso, o cardápio vai para revisão humana — os dados são salvos nos dois casos."
    )


def render_table(items: pd.DataFrame, filename: str) -> None:
    if items.empty:
        st.info("Nenhum item disponível para exportar nesta extração.")
        return
    df = items.copy()
    df["Alertas"] = [", ".join(item_flags(r)) for r in df.to_dict("records")]
    view = df[["category", "item_name", "variant_label", "price", "description", "attributes", "Alertas"]].rename(
        columns={"category": "Categoria", "item_name": "Item", "variant_label": "Variação", "price": "Preço",
                 "description": "Descrição", "attributes": "Atributos"})
    st.dataframe(view, hide_index=True, width="stretch",
                 column_config={"Preço": st.column_config.NumberColumn(format="%.2f")})
    st.download_button("Baixar itens deste cardápio (CSV)", items.to_csv(index=False).encode("utf-8"),
                       f"{filename.rsplit('.', 1)[0]}_itens.csv", "text/csv")


def usd(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    return f"US$ {v:.4f}".replace(".", ",")


def verdict(run: dict, validation: dict | None) -> None:
    status = run["status"]
    detail_html = ""
    if run.get("is_menu") in (False, "False"):
        title, detail = "Isto não parece um cardápio", "O modelo não encontrou itens de cardápio na imagem."
    elif validation:
        failed = [c["check"] for c in validation["checks"] if not c["success"]]
        title = "Aprovado pelos guardrails" if status == "aprovado" else "Precisa de revisão humana"
        detail = f'{validation["passed"]} de {validation["total"]} verificações passaram.'
        if failed:
            detail += " Estas não passaram:"
            detail_html = "".join(f"<li>{e(f)}</li>" for f in failed)
    else:
        title = STATUS_TXT.get(status, status)
        detail = f'{int(run.get("gx_passed", 0))} de {int(run.get("gx_total", 0))} verificações passaram.'
    falhas = f"<ul>{detail_html}</ul>" if validation and detail_html else ""
    st.markdown(f'<div class="veredito {status}"><strong>{e(title)}</strong><span>{e(detail)}</span>{falhas}</div>',
                unsafe_allow_html=True)
    cost = run.get("cost_usd")
    tok_in = f'{int(run["input_tokens"]):,}'.replace(",", ".")
    tok_out = f'{int(run["output_tokens"]):,}'.replace(",", ".")
    st.markdown(
        '<div class="fatos">'
        f'<span><b>{int(run["n_items"])}</b> itens em <b>{int(run["n_categories"])}</b> categorias</span>'
        f'<span><b>{br(run["latency_s"])} s</b> do envio ao CSV</span>'
        f'<span><b>{tok_in}</b> + <b>{tok_out}</b> tokens</span>'
        + (f'<span><b>{usd(cost)}</b></span>' if cost is not None and pd.notna(cost) else '<span>custo: preencha os preços no .env</span>')
        + f'<span>legibilidade <b>{e(str(run.get("legibility") or "—"))}</b></span>'
        "</div>",
        unsafe_allow_html=True,
    )


def find_image(name: str):
    for d in (config.UPLOADS_DIR, config.DATA_DIR):
        if (d / name).exists():
            return str(d / name)
    return None


# ------------------------------------------------------------------ cabeçalho
st.markdown(
    '<div class="brandbar"><div class="brandname"><span class="brandmark">◈</span>Cardápios</div>'
    '<div class="brandmeta">Seu workspace de extração</div></div>'
    '<div class="hero"><div class="hero-copy"><div class="eyebrow">DA IMAGEM À INFORMAÇÃO</div>'
    '<h1>Seu cardápio, organizado.</h1>'
    '<p>Transforme fotos em produtos, preços e categorias.<br>Confira cada detalhe e leve seus dados para o próximo passo.</p></div>'
    '<div class="hero-aside"><strong>Simples de enviar.<br>Fácil de conferir.</strong>'
    '<span>Extração com inteligência artificial</span></div></div>',
    unsafe_allow_html=True,
)
tab_one, tab_batch = st.tabs(["Transcrever cardápios", "Lote e métricas"])

# ------------------------------------------------------------------ transcrever
def error_hint(msg: str) -> str:
    return ("Coloque sua chave em backend/.env (OPENAI_API_KEY) e reinicie o app."
            if "OPENAI_API_KEY" in msg else "Tente novamente; se persistir, use uma foto mais nítida.")


def show_result(res: dict, filename: str) -> None:
    """Veredito + abas com o cardápio, as verificações, a tabela e o JSON do modelo."""
    items = pd.DataFrame(res["items"])
    verdict(res["run"], res["validation"])
    t_menu, t_checks, t_table, t_json = st.tabs(["Cardápio", "Verificações", "Tabela", "JSON do modelo"])
    with t_menu:
        render_menu(items, res["run"].get("restaurant_name"), res["run"].get("notes"))
    with t_checks:
        render_checks(res["validation"])
    with t_table:
        render_table(items, filename)
    with t_json:
        st.json(res["menu"], expanded=2)


def single_ui(up) -> None:
    """Uma foto: mostra cada etapa do pipeline enquanto roda."""
    if st.session_state.get("result_file") != up.file_id:
        st.session_state.pop("result", None)

    col_photo, col_out = st.columns([5, 7], gap="large")
    with col_photo:
        st.image(up, width="stretch")
        kb = f"{up.size / 1024:,.0f}".replace(",", ".")
        st.caption(f"{up.name}, {kb} KB")

    with col_out:
        if "result" in st.session_state:
            show_result(st.session_state["result"], up.name)
            if st.button("Transcrever de novo", width="content"):
                st.session_state.pop("result", None)
                st.rerun()
            return

        go = st.button("Transcrever cardápio", type="primary", width="stretch")
        st.caption("Leva de 10 a 30 segundos, dependendo do tamanho do cardápio.")
        if not go:
            return
        data = up.getvalue()
        (config.UPLOADS_DIR / up.name).write_bytes(data)
        labels = dict(STEPS)
        order = [k for k, _ in STEPS]
        with st.status("Transcrevendo…", expanded=True) as box:
            lines = {k: st.empty() for k in order}
            for i, (k, label) in enumerate(STEPS, 1):
                lines[k].markdown(f"<span style='opacity:.5'>{i}. {e(label)}</span>", unsafe_allow_html=True)
            t0 = time.perf_counter()

            def on_step(step):
                idx = order.index(step)
                for j, k in enumerate(order[:idx]):
                    lines[k].markdown(f"✓ {j + 1}. {e(labels[k])}")
                lines[step].markdown(f"**{idx + 1}. {e(labels[step])}…**")

            flow.progress_hook = on_step
            try:
                res = flow.menu_pipeline(data, up.name)
            except Exception as exc:
                box.update(label="Não foi possível transcrever", state="error", expanded=True)
                st.error(f"{exc}\n\n{error_hint(str(exc))}")
                res = None
            finally:
                flow.progress_hook = None
            if res:
                for j, k in enumerate(order):
                    lines[k].markdown(f"✓ {j + 1}. {e(labels[k])}")
                box.update(label=f"Transcrito em {br(time.perf_counter() - t0)} s", state="complete", expanded=False)
                st.session_state["result"] = res
                st.session_state["result_file"] = up.file_id
                st.rerun()


def batch_table(results: list[dict]) -> pd.DataFrame:
    rows = []
    for r in results:
        run = r["res"]["run"] if r["res"] else {}
        rows.append({
            "Arquivo": r["file"],
            "Status": STATUS_TXT.get(run.get("status"), "Erro"),
            "Itens": run.get("n_items"),
            "Verificações": f'{run["gx_passed"]}/{run["gx_total"]}' if run else "—",
            "Tempo (s)": run.get("latency_s"),
            "Custo (US$)": run.get("cost_usd"),
            "Observação": r["error"] or run.get("notes"),
        })
    return pd.DataFrame(rows)


BATCH_COLS = {"Tempo (s)": st.column_config.NumberColumn(format="%.1f"),
              "Custo (US$)": st.column_config.NumberColumn(format="%.4f")}


def batch_ui(ups: list) -> None:
    """Várias fotos: processa uma por vez, com barra de progresso e tabela parcial."""
    key = tuple(u.file_id for u in ups)
    if st.session_state.get("batch_key") != key:
        st.session_state.pop("batch", None)
    n = len(ups)
    results = st.session_state.get("batch")

    if results is None:
        st.markdown(f"**{n} fotos selecionadas**")
        cols = st.columns(6)
        for i, u in enumerate(ups):
            with cols[i % 6]:
                st.image(u, width="stretch")
                st.caption(u.name)
        go = st.button(f"Transcrever {n} cardápios", type="primary")
        st.caption(f"Um cardápio por vez, de 10 a 30 segundos cada: cerca de {max(1, round(n * 20 / 60))} min "
                   "no total. Não feche a aba enquanto o lote roda.")
        if not go:
            return
        results = []
        t0 = time.perf_counter()
        bar = st.progress(0.0)
        live = st.empty()
        for i, u in enumerate(ups):
            bar.progress(i / n, text=f"{i + 1} de {n}: lendo {u.name}…")
            data = u.getvalue()
            (config.UPLOADS_DIR / u.name).write_bytes(data)
            try:
                results.append({"file": u.name, "res": flow.menu_pipeline(data, u.name), "error": None})
            except Exception as exc:
                results.append({"file": u.name, "res": None, "error": str(exc)})
                if "OPENAI_API_KEY" in str(exc):  # sem chave, nenhum dos próximos vai funcionar
                    st.error(f"{exc}\n\n{error_hint(str(exc))}")
                    break
            live.dataframe(batch_table(results), hide_index=True, width="stretch", column_config=BATCH_COLS)
        bar.progress(1.0, text=f"{len(results)} de {n} cardápios em {br(time.perf_counter() - t0)} s")
        st.session_state["batch"] = results
        st.session_state["batch_key"] = key
        st.rerun()

    ok = [r for r in results if r["res"]]
    aprov = sum(r["res"]["run"]["status"] == "aprovado" for r in ok)
    custo = sum(r["res"]["run"].get("cost_usd") or 0 for r in ok)
    tempo = sum(r["res"]["run"]["latency_s"] for r in ok)
    st.markdown(
        '<div class="fatos">'
        f'<span><b>{len(results)}</b> cardápios processados</span>'
        f'<span><b>{aprov}</b> aprovados</span>'
        f'<span><b>{len(ok) - aprov}</b> em revisão</span>'
        f'<span><b>{len(results) - len(ok)}</b> com erro</span>'
        f'<span><b>{br(tempo)} s</b> no total</span>'
        + (f'<span><b>{usd(custo)}</b> no total</span>' if custo else "")
        + "</div>",
        unsafe_allow_html=True,
    )
    event = st.dataframe(batch_table(results), hide_index=True, width="stretch", on_select="rerun",
                         selection_mode="single-row", column_config=BATCH_COLS)
    st.caption("Clique em uma linha para ver o cardápio transcrito ao lado da foto. "
               "Tudo já foi salvo no CSV consolidado e entra nas métricas da aba ao lado.")
    if st.button("Transcrever de novo", width="content"):
        st.session_state.pop("batch", None)
        st.rerun()

    rows = event.selection.rows if event and event.selection else []
    if rows:
        r = results[rows[0]]
        a, b = st.columns([5, 7], gap="large")
        with a:
            up = next((u for u in ups if u.name == r["file"]), None)
            if up:
                st.image(up, width="stretch")
            st.caption(r["file"])
        with b:
            if r["res"]:
                show_result(r["res"], r["file"])
            else:
                st.error(f"Este cardápio falhou: {r['error']}")


with tab_one:
    ups = st.file_uploader(
        "Envie a foto de um ou mais cardápios",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Foto de celular serve. A rotação é corrigida automaticamente.",
    )
    if not ups:
        for k in ("result", "batch"):
            st.session_state.pop(k, None)
        st.markdown(
            '<div class="steps"><div class="step"><small>01 / ENVIE</small><strong>Comece com uma foto</strong>'
            '<p>Selecione um cardápio ou envie várias imagens de uma vez.</p></div>'
            '<div class="step"><small>02 / CONFIRA</small><strong>Uma leitura organizada</strong>'
            '<p>Veja os itens extraídos e os detalhes que precisam de revisão.</p></div>'
            '<div class="step"><small>03 / EXPORTE</small><strong>Seus dados prontos para usar</strong>'
            '<p>Baixe a tabela e acompanhe os resultados do processamento.</p></div></div>',
            unsafe_allow_html=True,
        )
    elif len(ups) == 1:
        single_ui(ups[0])
    else:
        batch_ui(ups)

# ------------------------------------------------------------------ lote
with tab_batch:
    m = compute_metrics()
    runs = storage.read_runs()
    if not m["menus_processados"]:
        st.info("Nenhum cardápio processado ainda. Transcreva um na primeira aba ou rode o lote:\n\n"
                "`.venv\\Scripts\\python -m scripts.run_batch`")
    else:
        st.subheader("Métricas exigidas no relatório")
        c = st.columns(4)
        c[0].metric("Dados faltando", f"{br(m['pct_missing_data'], 2)}%",
                    help="Percentual de campos obrigatórios (categoria, item, preço) vazios após a extração.")
        c[1].metric("Preços razoáveis", f"{br(m['pct_precos_razoaveis'], 2)}%",
                    help=f"Percentual de todos os itens com preço entre {config.PRICE_MIN:g} e {config.PRICE_MAX:g}. Preços ausentes também entram no denominador. Fora da faixa indica necessidade de revisão.")
        c[2].metric("Tempo médio por cardápio", f"{br(m['latencia_media_s'])} s",
                    help="Do recebimento da imagem até a gravação no CSV.")
        c[3].metric("Custo médio por cardápio",
                    usd(m["custo_medio_usd"]) if m["custo_medio_usd"] is not None else "—",
                    help="Tokens consumidos × preço do modelo definido no .env.")
        n = m["menus_processados"]
        st.caption(
            f"{n} {'cardápio processado' if n == 1 else 'cardápios processados'}: "
            f"{m['menus_aprovados']} aprovados, {m['menus_revisao_humana']} em revisão e {m['menus_com_erro']} com erro. "
            f"{m['itens_extraidos']} itens extraídos"
            + (f", custo total de {usd(m['custo_total_usd'])}." if m["custo_total_usd"] else ".")
        )

        st.subheader("Cardápios processados")
        filtro = st.segmented_control("Mostrar", ["Todos", "Aprovados", "Em revisão", "Com erro"],
                                      default="Todos", label_visibility="collapsed")
        sel = {"Aprovados": "aprovado", "Em revisão": "revisao_humana", "Com erro": "erro"}.get(filtro)
        view = runs.iloc[::-1]
        if sel:
            view = view[view["status"] == sel]
        table = view.assign(
            Status=view["status"].map(STATUS_TXT),
            Verificações=view.apply(lambda r: f"{int(r.gx_passed)}/{int(r.gx_total)}" if pd.notna(r.gx_total) else "—", axis=1),
            Observação=view["error"].where(view["status"] == "erro", view["notes"]),
        )[["source_file", "Status", "n_items", "Verificações", "latency_s", "cost_usd", "Observação", "run_id"]]
        event = st.dataframe(
            table, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
            column_config={
                "source_file": "Arquivo", "n_items": st.column_config.NumberColumn("Itens"),
                "latency_s": st.column_config.NumberColumn("Tempo (s)", format="%.1f"),
                "cost_usd": st.column_config.NumberColumn("Custo (US$)", format="%.4f"),
                "run_id": None,
            },
        )
        st.caption("Clique em uma linha para ver o cardápio transcrito ao lado da foto.")

        rows = event.selection.rows if event and event.selection else []
        if rows:
            r = table.iloc[rows[0]]
            run = runs[runs["run_id"] == r["run_id"]].iloc[0].to_dict()
            if run["status"] == "erro":
                st.error(f"Este cardápio falhou: {run.get('error')}")
            else:
                items = storage.read_items()
                items = items[items["run_id"] == run["run_id"]]
                a, b = st.columns([5, 7], gap="large")
                with a:
                    img = find_image(run["source_file"])
                    if img:
                        st.image(img, width="stretch")
                    st.caption(run["source_file"])
                with b:
                    verdict(run, None)
                    render_menu(items, run.get("restaurant_name") if pd.notna(run.get("restaurant_name")) else None,
                                run.get("notes") if pd.notna(run.get("notes")) else None)

        if config.ITEMS_CSV.exists():
            st.download_button("Baixar CSV consolidado", config.ITEMS_CSV.read_bytes(), "menu_items.csv", "text/csv")


st.markdown('<div class="workspace-footer"><span>CARDÁPIOS / Extração com contexto.</span><span>PROJETO ACADÊMICO · CIÊNCIA DE DADOS E IA</span></div>', unsafe_allow_html=True)

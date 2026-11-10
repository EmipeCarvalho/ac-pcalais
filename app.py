import io
import json
import os
import time
from pathlib import Path
import pandas as pd
import streamlit as st
from pydantic import SecretStr
from PIL import Image
from dotenv import load_dotenv
from menu_atlas.pipeline import process_menu
from menu_atlas.storage import tables, summarize
load_dotenv()
st.set_page_config(page_title="Menu Atlas — Da imagem ao dado", page_icon="◈", layout="wide")
st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;450;500;600;700;800&display=swap');
html,body,[class*="css"],.stApp,p,h1,h2,h3,button,input,label{font-family:'Inter',sans-serif!important}
.block-container{max-width:1440px;padding:2.5rem 3.5rem 4rem} h1{font-size:3.2rem!important;letter-spacing:-.065em;font-weight:700!important;line-height:1.09!important} h2{letter-spacing:-.04em} h3{letter-spacing:-.03em}
[data-testid="stSidebar"]{background:#102F27} [data-testid="stSidebar"] *{color:#E6EFE7} [data-testid="stSidebar"] input{color:#172B26}
[data-testid="stMetric"]{background:#fff;border:1px solid #E1E7DD;border-radius:16px;padding:20px}
[data-testid="stMetricValue"]{font-size:1.9rem;letter-spacing:-.04em}
[data-testid="stFileUploader"]{background:white;border:1px solid #DDE5DB;border-radius:18px;padding:18px}
.stButton>button{border-radius:10px;min-height:45px;font-weight:600} .stDownloadButton>button{border-radius:10px}
.eyebrow{font-size:11px;letter-spacing:.16em;font-weight:700;color:#63806F;margin-bottom:20px}
.hero-note{color:#6A7D72;font-size:16px;max-width:550px;line-height:1.7;margin:22px 0 34px}
.pill{display:inline-block;padding:7px 12px;border-radius:25px;background:#E8EEDF;color:#41623D;font-size:11px;font-weight:600;margin:0 6px 8px 0}
.brand{font-size:24px;font-weight:700;letter-spacing:-1px;margin-bottom:4px}.brand-sub{opacity:.55;font-size:11px;letter-spacing:2px;margin-bottom:36px}
.guide{background:#E9EEDF;border:1px solid #DCE4D3;padding:25px;border-radius:18px;margin-top:25px;color:#3D593E}
.footer{color:#829084;font-size:11px;margin-top:55px;border-top:1px solid #DFE5DC;padding-top:18px}
</style>''', unsafe_allow_html=True)
db = os.getenv("DB_PATH", "data/menu_atlas.sqlite")
with st.sidebar:
    st.markdown('<div class="brand">◈ Menu Atlas</div><div class="brand-sub">DA IMAGEM AO DADO</div>', unsafe_allow_html=True)
    page = st.radio("Workspace", ["Extrair cardápio", "Biblioteca", "Qualidade & avaliação", "Sobre o projeto"], label_visibility="collapsed")
    st.divider()
    st.caption("CONEXÃO COM A IA")
    st.caption("Gemini 2.5 Flash · compatível com plano gratuito, sujeito às cotas do projeto")
    key = st.text_input("Chave Gemini", type="password", help="Usada nesta sessão. Não é gravada no banco.")
    model = st.text_input("Modelo", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    cap = st.number_input("Preço máximo razoável", min_value=1.0, value=float(os.getenv("MAX_REASONABLE_PRICE", "1000")))
    st.caption("Ajuste à moeda e ao tipo de restaurante do seu conjunto.")
    st.link_button("Obter chave no Google AI Studio", "https://aistudio.google.com/api-keys")
    st.divider()
    st.caption("PROJETO ACADÊMICO · IBMEC\n\nExtração e Preparação de Dados")

def fmt(value, suffix=""):
    return "—" if value is None or pd.isna(value) else f"{value:,.2f}{suffix}"

def show_result(run):
    if run["status"] == "failed":
        st.error(run["error"])
        st.info("Verifique a chave e se o modelo está disponível na sua conta. O envio pode ser tentado novamente.")
        return
    q=run["quality"]
    if q["needs_review"]:
        st.warning("Extração concluída com itens ou observações para revisão. Consulte os alertas antes de usar os dados.")
    else:
        st.success("Extração concluída. Todos os itens passaram pelas regras configuradas.")
    cols=st.columns(4)
    for c,label,value in zip(cols,["Itens encontrados","Campos ausentes","Preços razoáveis","Tempo total"],[str(q["item_count"]),fmt(q["missing_pct"],"%"),fmt(q["reasonable_price_pct"],"%"),fmt(run["elapsed_seconds"]," s")]):
        c.metric(label,value)
    st.subheader(run["extraction"]["menu"].get("restaurant") or "Cardápio processado")
    a,b,c=st.tabs(["Itens estruturados", "Validações", "JSON original"])
    with a:
        df=pd.DataFrame(q["items"])
        if len(df):
            st.dataframe(df, hide_index=True, use_container_width=True)
            valid=df[df.status == "valid"]
            st.download_button("Baixar itens aprovados · CSV", valid.to_csv(index=False).encode("utf-8-sig"), "itens_aprovados.csv", "text/csv")
        else:
            st.info("Nenhum item identificado. Experimente uma foto mais nítida e com o cardápio inteiro.")
    with b:
        for warning in run["extraction"]["menu"]["warnings"]:
            st.warning(warning)
        st.dataframe(pd.DataFrame(q["checks"]), hide_index=True, use_container_width=True)
        st.caption("Regras verificam plausibilidade e consistência. Não comprovam fidelidade à imagem.")
    with c:
        st.json(run["extraction"]["menu"])
    st.download_button("Baixar extração e auditoria · JSON", json.dumps(run,ensure_ascii=False,indent=2),"extracao.json","application/json")

if page == "Extrair cardápio":
    st.markdown('<div class="eyebrow">WORKSPACE / NOVA EXTRAÇÃO</div>',unsafe_allow_html=True)
    left,right=st.columns([1.5,1],gap="large")
    with left:
        st.markdown("# O próximo passo do seu\ncardápio é ser dado.")
        st.markdown('<div class="hero-note">Transforme fotos em um catálogo organizado. A IA lê, a qualidade verifica e você acompanha cada resultado.</div><span class="pill">Leitura multimodal</span><span class="pill">Validação automática</span><span class="pill">Exportação em um clique</span>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="guide"><b>Uma imagem. Um fluxo completo.</b><p style="margin-top:15px;line-height:2;font-size:14px">01 &nbsp; Envie uma foto do cardápio<br>02 &nbsp; Extraia produtos, categorias e preços<br>03 &nbsp; Confira a qualidade e exporte</p></div>',unsafe_allow_html=True)
    st.write("")
    uploads=st.file_uploader("Adicione seus cardápios",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,help="Até 20 MB por imagem. Você também pode processar um lote.")
    st.caption("PNG, JPG ou WebP · Envie imagens nítidas, com os preços visíveis.")
    if uploads:
        with st.expander(f"Prévia · {len(uploads)} imagem(ns)"):
            for upload in uploads[:3]:
                try: st.image(Image.open(io.BytesIO(upload.getvalue())),caption=upload.name,width=350)
                except Exception: st.warning(f"Não foi possível abrir {upload.name}.")
        if st.button("Extrair cardápios  ↗",type="primary",disabled=not(key or os.getenv("GEMINI_API_KEY"))):
            results=[]
            bar=st.progress(0)
            with st.status("Processando cardápios…",expanded=True) as status:
                for i, upload in enumerate(uploads):
                    st.write(f"{i+1}/{len(uploads)} · {upload.name}")
                    results.append(process_menu(upload.getvalue(),upload.name,db,SecretStr(key) if key else None,model,cap))
                    bar.progress((i+1)/len(uploads))
                status.update(label="Processamento finalizado",state="complete",expanded=False)
            st.session_state["results"]=results
    if not(key or os.getenv("GEMINI_API_KEY")):
        st.info("Informe sua chave Gemini na lateral para habilitar a extração.")
    for run in st.session_state.get("results",[]):
        with st.container(border=True): show_result(run)
elif page == "Biblioteca":
    st.markdown('<div class="eyebrow">WORKSPACE / BIBLIOTECA</div>',unsafe_allow_html=True)
    st.title("Cada cardápio, uma nova camada.")
    st.write("Seu histórico de extrações e os dados que passaram pela validação.")
    runs,items=tables(db)
    if runs.empty: st.info("Sua biblioteca começa na primeira extração.")
    else:
        st.dataframe(runs[["id","created_at","source","restaurant","status","item_count","elapsed_seconds"]],hide_index=True,use_container_width=True)
        selected=st.selectbox("Inspecionar execução",runs.id.tolist())
        selected_run=runs[runs.id == selected].iloc[0]
        st.dataframe(items[items.run_id == selected],hide_index=True,use_container_width=True)
        with st.expander("Auditoria da execução"):
            st.json(json.loads(selected_run.validation_json))
        if len(items):
            valid=items[items.status == "valid"]
            st.download_button("Exportar catálogo aprovado · CSV",valid.to_csv(index=False).encode("utf-8-sig"),"catalogo.csv","text/csv")
        st.download_button("Baixar banco SQLite",Path(db).read_bytes(),"menu_atlas.sqlite","application/vnd.sqlite3")
elif page == "Qualidade & avaliação":
    st.markdown('<div class="eyebrow">WORKSPACE / QUALIDADE</div>',unsafe_allow_html=True)
    st.title("Qualidade que você consegue medir.")
    st.write("Métricas calculadas sobre os dados brutos extraídos, antes de excluir itens com erro.")
    runs,items=tables(db)
    if runs.empty: st.info("Processe cardápios para visualizar os indicadores reais.")
    else:
        metrics=summarize(runs)
        cols=st.columns(4)
        for c,label,value in zip(cols,["Campos ausentes","Preços razoáveis","Latência média","Custo médio / cardápio"],[fmt(metrics["missing_pct"],"%"),fmt(metrics["reasonable_price_pct"],"%"),fmt(metrics["mean_latency_seconds"]," s"),fmt(metrics["mean_cost_usd"]," USD")]): c.metric(label,value)
        st.write(f"{metrics['attempts']} execuções · {metrics['processed']} processadas · {metrics['failed']} falhas · {metrics['items']} itens")
        unique=runs[runs.status != "failed"].image_sha256.nunique()
        st.progress(min(unique/50,1),text=f"{unique}/50 imagens distintas processadas — meta da atividade")
        st.bar_chart(runs.status.value_counts(),color="#166B52")
        st.caption("Latência: leitura recebida até commit no banco. Custos desconhecidos aparecem como —. Configure tarifas no .env. Reexecuções entram nas médias; use banco separado para o lote final.")
        st.download_button("Baixar indicadores · JSON",json.dumps(metrics,indent=2,ensure_ascii=False,allow_nan=False),"indicadores.json","application/json")
else:
    st.markdown('<div class="eyebrow">WORKSPACE / PROJETO</div>',unsafe_allow_html=True)
    st.title("Da fotografia à informação confiável.")
    st.write("POC para a disciplina Extração e Preparação de Dados. Arquitetura inspirada no estudo de caso da DoorDash.")
    st.markdown("**Prefect** orquestra preparação, extração multimodal, validação com **Great Expectations** e persistência em **SQLite**. A interface usa **Streamlit**.")
    st.markdown("**Revisão humana:** itens inválidos ficam identificados e preservados para auditoria. A exportação aprovada inclui apenas itens válidos. A comparação com a foto deve ser feita antes da entrega final.")
    st.markdown("**Limitações:** sombras, reflexos, baixa resolução e múltiplas colunas podem prejudicar a leitura. Preços plausíveis ainda podem estar errados; as regras não substituem conferência visual. Moedas diferentes precisam de limites adequados.")
st.markdown('<div class="footer">MENU ATLAS &nbsp; / &nbsp; Extração com contexto. Dados com critério.</div>',unsafe_allow_html=True)

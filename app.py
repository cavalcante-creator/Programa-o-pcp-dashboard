import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date
import json

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0sYky_AQVQN7NMv0MK55UngaBm7ayey1mJB37BE7lB6rNjmUvUJ68FD0-qsPe-vgT/exec"

st_autorefresh(interval=60000)
st.set_page_config(layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
.header { display: flex; align-items: center; justify-content: space-between; }
.logo { width: 200px; margin-top: 10px; }
.titulo { flex-grow: 1; text-align: center; font-size: 26px; font-weight: 600; }
.vazio { width: 140px; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
<img class="logo" src="https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png">
<div class="titulo">Planejamento PCP</div>
<div class="vazio"></div>
</div>
""", unsafe_allow_html=True)

# ─── CARREGA RANCHOS DO GOOGLE SHEETS ─────────────────────────────────
@st.cache_data(ttl=60)
def carregar_ranchos():
    try:
        r = requests.get(APPS_SCRIPT_URL, params={"acao": "listar"}, timeout=10)
        return r.json()
    except:
        return {}

ranchos_atuais = carregar_ranchos()

# ─── DADOS GOOGLE SHEETS ──────────────────────────────────────────────
sheet_id = "1eQHvLVw-WLsA4UruaM6GThcy0dgb5ONNAn8AZ_KwBuU"

abas = [
    "BASE_LINHA_1","BASE_LINHA_2","BASE_LINHA_3",
    "BASE_AREA_LIQUIDA",
    "BASE_REJUNTE_MAQUINA_1","BASE_REJUNTE_MAQUINA_2","BASE_REJUNTE_MAQUINA_3"
]

dados_total = []

for aba in abas:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={aba}"
    response = requests.get(url)
    f = StringIO(response.text)
    reader = csv.DictReader(f)
    for linha in reader:
        linha["Linha"] = aba
        dados_total.append(linha)

def nome_linha(linha):
    return linha.replace("BASE_", "").replace("_", " ")

def get_semana(data_str):
    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y")
        ano, semana, _ = dt.isocalendar()
        return f"Semana {semana}/{ano}"
    except:
        return ""

def to_float(valor):
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except:
        return 0

def limpar_status(s):
    if not s:
        return ""
    s = str(s).strip().upper()
    if "AGUARDANDO" in s: return "AGUARDANDO"
    if "PRODUÇÃO" in s: return "EM PRODUÇÃO"
    if "LIBERADA" in s: return "LIBERADA"
    return s

estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data_original = item.get("Data", "")
    nova_data = str(item.get("Nova Data", "")).strip()
    turno = item.get("Turno", "Sem Turno")
    data_usar = nova_data if nova_data else data_original
    estrutura.setdefault(linha, {}).setdefault(data_usar, {}).setdefault(turno, []).append(item)

col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida, format="DD/MM/YYYY")
turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

semanas_disponiveis = sorted(set(get_semana(i.get("Data")) for i in dados_total if i.get("Data")))
semanas_sel = col4.multiselect("📆 Semanas", semanas_disponiveis)

ordem_pesquisa = col5.text_input("🔎 Buscar Ordem")
produto_pesquisa = col6.text_input("🔎 Buscar Produto")

status_lista = sorted(set(limpar_status(i.get("Status")) for i in dados_total if i.get("Status")))
status_sel = col7.selectbox("📌 Status", ["Todos"] + status_lista)

colb1, colb2 = st.columns(2)

if colb1.button("Hoje"):
    st.session_state.data_escolhida = date.today()
    data_input = date.today()

mostrar_todas = colb2.checkbox("Mostrar todas as datas", value=True)

data_sel = data_input.strftime("%d/%m/%Y")

# ─── JSON DOS RANCHOS PARA O JS ────────────────────────────────────────
ranchos_meta_json = json.dumps({k: {"numero": v.get("numero",""), "nome": v.get("nome","")} for k, v in ranchos_atuais.items()})
ranchos_b64_json  = json.dumps({k: v.get("base64","") for k, v in ranchos_atuais.items()})
apps_script_url   = APPS_SCRIPT_URL

html = f"""
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>

<style>
body {{ font-family: 'Segoe UI'; background: #f5f7fa; margin: 20px; }}

.linha h2 {{
    background: #2c3e50;
    color: white;
    padding: 10px;
    border-radius: 8px;
}}

.cards {{ display: flex; flex-wrap: wrap; }}

.card {{
    width: 260px;
    padding: 12px;
    margin: 8px;
    border-radius: 12px;
    background: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
    border-left: 5px solid transparent;
}}

.producao {{ border-left: 5px solid #a9cce3; background: #f4f9fd; }}
.pendente {{ border-left: 5px solid #f5b7b1; background: #fdf2f2; }}
.finalizado {{ border-left: 5px solid #a9dfbf; background: #f3fbf6; }}
.reprogramado {{ border-left: 5px solid #d7bde2; background: #f8f4fb; }}
.liberada {{ border-left: 5px solid #f

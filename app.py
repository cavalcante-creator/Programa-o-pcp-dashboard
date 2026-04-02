import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date
import base64

# 🔄 Auto refresh
st_autorefresh(interval=60000)

st.set_page_config(layout="wide")

# 🎨 HEADER
st.markdown("""
<style>
.block-container { padding-top: 0.2rem; }

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo { width: 180px; }

.titulo {
    flex-grow: 1;
    text-align: center;
    font-size: 26px;
    font-weight: 600;
}
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

# 🔗 GOOGLE SHEETS
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

# 🔧 FUNÇÕES
def nome_linha(linha):
    return linha.replace("BASE_", "").replace("_", " ")

def get_semana(data_str):
    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y")
        ano, semana, _ = dt.isocalendar()
        return f"Semana {semana}/{ano}"
    except:
        return ""

# 🔧 ESTRUTURA
estrutura = {}
for item in dados_total:
    linha = nome_linha(item["Linha"])
    data = item.get("Data", "")
    turno = item.get("Turno", "Sem Turno")

    estrutura.setdefault(linha, {}).setdefault(data, {}).setdefault(turno, []).append(item)

# 🔽 FILTROS
col1, col2, col3, col4 = st.columns(4)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida, format="DD/MM/YYYY")

turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

semanas_disponiveis = sorted(set(get_semana(i.get("Data")) for i in dados_total if i.get("Data")))
semanas_sel = col4.multiselect("📆 Semanas", semanas_disponiveis)

# 🔽 LINHA DE BAIXO
colb1, colb2, colb3, colb4 = st.columns(4)

if colb1.button("Hoje"):
    st.session_state.data_escolhida = date.today()
    data_input = date.today()

mostrar_todas = colb2.checkbox("Mostrar todas", False)

data_sel = "Todas" if mostrar_todas else data_input.strftime("%d/%m/%Y")

# 🔥 HTML PRINCIPAL
html = """
<html>
<head>
<style>
body { font-family: Arial; background:#f5f7fa; }

.linha { page-break-inside: avoid; }

.linha h2 {
    background:#2c3e50;
    color:white;
    padding:8px;
    border-radius:6px;
}

.card {
    display:inline-block;
    width:250px;
    margin:6px;
    padding:10px;
    border-radius:10px;
    background:white;
    box-shadow:0 3px 10px rgba(0,0,0,0.1);
}

.falta { border-left:5px solid red; }
.ok { border-left:5px solid green; }
.sobra { border-left:5px solid orange; }
.atrasado { border-left:5px solid darkred; }

/* 🖨️ MODO IMPRESSÃO */
@media print {
    button { display:none; }
    body { background:white; }
}
</style>
</head>
<body>
"""

# 🔄 LOOP
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    html += f"<div class='linha'><h2>{linha}</h2>"

    for data, turnos in datas.items():

        if semanas_sel and get_semana(data) not in semanas_sel:
            continue

        if data_sel != "Todas" and data != data_sel:
            continue

        html += f"<h4>{data}</h4>"

        for turno, itens in turnos.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            for item in itens:
                status = item.get("Status","").lower()

                classe = "ok"
                if "falta" in status: classe="falta"
                elif "sobra" in status: classe="sobra"
                elif "atras" in status: classe="atrasado"

                html += f"""
                <div class='card {classe}'>
                <b>{item.get("Produto")}</b><br>
                Ordem: {item.get("Ordem")}<br>
                Qtde: {item.get("Qtde Total")}<br>
                Status: {item.get("Status")}
                </div>
                """

    html += "</div>"

html += "</body></html>"

# 🚀 EXIBIR
st.components.v1.html(html, height=800, scrolling=True)

# 🖨️ EXPORTAR PDF (PROFISSIONAL)
if colb4.button("📄 Exportar PDF"):
    html_print = f"""
    <html>
    <head>
        <script>
            window.onload = function() {{
                window.print();
            }}
        </script>
    </head>
    {html}
    </html>
    """

    b64 = base64.b64encode(html_print.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" target="_blank">Clique aqui para abrir o PDF</a>'
    st.markdown(href, unsafe_allow_html=True)

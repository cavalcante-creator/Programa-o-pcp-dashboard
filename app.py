import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime

# 🔄 Atualiza automático a cada 60s
st_autorefresh(interval=60000)

st.set_page_config(layout="wide")
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}

/* Container do topo */
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Logo esquerda */
.logo {
    width: 200px;  /* AUMENTA A LOGO */
}

.titulo {
    flex-grow: 1;
    text-align: center;
    font-size: 28px;  /* DIMINUI O TÍTULO */
    font-weight: 600;
}
}

/* Espaço direita (pra centralizar de verdade) */
.vazio {
    width: 140px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <img class="logo" src="https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png">
    <div class="titulo">📊 Planejamento PCP</div>
    <div class="vazio"></div>
</div>
""", unsafe_allow_html=True)

sheet_id = "1eQHvLVw-WLsA4UruaM6GThcy0dgb5ONNAn8AZ_KwBuU"

abas = [
    "BASE_LINHA_1",
    "BASE_LINHA_2",
    "BASE_LINHA_3",
    "BASE_AREA_LIQUIDA",
    "BASE_REJUNTE_MAQUINA_1",
    "BASE_REJUNTE_MAQUINA_2",
    "BASE_REJUNTE_MAQUINA_3"
]

dados_total = []

# 🔄 BUSCAR DADOS
for aba in abas:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={aba}"
    response = requests.get(url)
    f = StringIO(response.text)
    reader = csv.DictReader(f)

    for linha in reader:
        linha["Linha"] = aba
        dados_total.append(linha)

# 🔧 ORGANIZAÇÃO
def nome_linha(linha):
    return linha.replace("BASE_", "").replace("_", " ")

estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data = item.get("Data", "")
    turno = item.get("Turno", "Sem Turno")

    estrutura.setdefault(linha, {}).setdefault(data, {}).setdefault(turno, []).append(item)

# 🔽 FILTROS STREAMLIT
col1, col2, col3 = st.columns(3)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
datas = sorted(set(i["Data"] for i in dados_total if i["Data"]))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("Linha", ["Todas"] + linhas)
data_sel = col2.selectbox("Data", ["Todas"] + datas)
turno_sel = col3.selectbox("Turno", ["Todos"] + turnos)

# 🔥 HTML (SEU LAYOUT ORIGINAL)
html = """
<html>
<head>
<style>
body {
    font-family: 'Segoe UI', Arial;
    background: #f5f7fa;
    margin: 20px;
}

.linha h2 {
    background: #2c3e50;
    color: white;
    padding: 10px;
    border-radius: 8px;
    font-weight: 500;
}

.cards {
    display: flex;
    flex-wrap: wrap;
}

.card {
    width: 260px;
    padding: 12px;
    margin: 8px;
    border-radius: 12px;
    font-size: 13px;
    background: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    border-left: 5px solid transparent;
}

.falta { border-left: 5px solid #e74c3c; }
.ok { border-left: 5px solid #2ecc71; }
.sobra { border-left: 5px solid #f1c40f; }
.atrasado { border-left: 5px solid #c0392b; }

</style>
</head>
<body>
"""

# 🔄 CONSTRUIR HTML COM FILTRO
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    html += f"<div class='linha'><h2>{linha}</h2>"

    for data, turnos in datas.items():

        if data_sel != "Todas" and data != data_sel:
            continue

        html += f"<h3>📅 {data}</h3>"

        for turno, itens in turnos.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            html += f"<b>Turno: {turno}</b><div class='cards'>"

            for item in itens:
                status = item.get("Status", "").lower()

                if "falta" in status:
                    classe = "falta"
                elif "sobra" in status:
                    classe = "sobra"
                elif "atras" in status:
                    classe = "atrasado"
                else:
                    classe = "ok"

                html += f"""
                <div class='card {classe}'>
                <b>{item.get("Produto")}</b><br>
                Ordem: {item.get("Ordem")}<br>
                Qtde: {item.get("Qtde Total")}<br>
                Status: {item.get("Status")}
                </div>
                """

            html += "</div>"

    html += "</div>"

html += "</body></html>"

# 🚀 MOSTRAR NA WEB
st.components.v1.html(html, height=2000, scrolling=True)

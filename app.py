import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO, BytesIO
from datetime import datetime, date
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# 🔄 Auto refresh
st_autorefresh(interval=60000)

st.set_page_config(layout="wide")

# 🎨 ESPAÇO
st.markdown("""
<style>
.block-container {
    padding-top: 0.2rem;
}
</style>
""", unsafe_allow_html=True)

# 🎨 HEADER
st.markdown("""
<style>
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: -10px;
}

.logo {
    width: 200px;
}

.titulo {
    flex-grow: 1;
    text-align: center;
    font-size: 26px;
    font-weight: 600;
}

.vazio {
    width: 140px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <img class="logo" src="https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png">
    <div class="titulo"> Planejamento PCP</div>
    <div class="vazio"></div>
</div>
""", unsafe_allow_html=True)

# 🔗 GOOGLE SHEETS
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

# 🔽 FILTROS
col1, col2, col3 = st.columns(3)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input(
    "📅 Selecionar data",
    value=st.session_state.data_escolhida,
    format="DD/MM/YYYY"
)

turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

# 🔽 LINHA DE BAIXO
colb1, colb2, colb3, colb4 = st.columns(4)

if colb1.button("Hoje"):
    st.session_state.data_escolhida = date.today()
    data_input = date.today()

mostrar_todas = colb2.checkbox("Mostrar todas as datas", value=False)

if mostrar_todas:
    data_sel = "Todas"
else:
    data_sel = data_input.strftime("%d/%m/%Y")

if not mostrar_todas:
    colb3.caption(f"📍 Data ativa: {data_sel}")

# 🔥 GERAR HTML + TEXTO PDF
html = ""
pdf_texto = []

for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    html += f"<h2>{linha}</h2>"
    pdf_texto.append(f"\n{linha}")

    for data, turnos in datas.items():

        if data_sel != "Todas" and data != data_sel:
            continue

        html += f"<h3>{data}</h3>"
        pdf_texto.append(f"  Data: {data}")

        for turno, itens in turnos.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            html += f"<b>Turno: {turno}</b><br>"
            pdf_texto.append(f"    Turno: {turno}")

            for item in itens:
                linha_txt = f"{item.get('Produto')} | Ordem: {item.get('Ordem')} | Qtde: {item.get('Qtde Total')} | Status: {item.get('Status')}"
                html += linha_txt + "<br>"
                pdf_texto.append("      " + linha_txt)

# 🚀 EXIBIR
st.markdown(html, unsafe_allow_html=True)

# 📄 GERAR PDF
def gerar_pdf(texto_lista):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()

    elementos = []

    for linha in texto_lista:
        elementos.append(Paragraph(linha, styles["Normal"]))
        elementos.append(Spacer(1, 6))

    doc.build(elementos)
    buffer.seek(0)
    return buffer

pdf_file = gerar_pdf(pdf_texto)

# 📥 BOTÃO DOWNLOAD
colb4.download_button(
    label="📄 Baixar PDF",
    data=pdf_file,
    file_name="planejamento_pcp.pdf",
    mime="application/pdf"
)

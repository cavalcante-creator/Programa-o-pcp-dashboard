import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date

# 🔄 Auto refresh
st_autorefresh(interval=60000)
st.set_page_config(layout="wide")

# 🎨 HEADER
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.logo {
    width: 200px;
    margin-top: 10px;
}
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

def to_float(valor):
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except:
        return 0

# 🔧 ORGANIZAÇÃO
estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data_original = item.get("Data", "")
    nova_data = str(item.get("Nova Data", "")).strip()
    turno = item.get("Turno", "Sem Turno")

    data_usar = nova_data if nova_data else data_original

    estrutura.setdefault(linha, {}).setdefault(data_usar, {}).setdefault(turno, []).append(item)

# 🔽 FILTROS
col1, col2, col3 = st.columns(3)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida, format="DD/MM/YYYY")

turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

# 🔥 HTML + PDF
html = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<style>
body { font-family: 'Segoe UI'; background: #f5f7fa; margin: 20px; }

.linha h2 {
    background: #2c3e50;
    color: white;
    padding: 10px;
    border-radius: 8px;
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
    background: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
    border-left: 5px solid transparent;
}

button {
    margin-top: 8px;
    padding: 6px 10px;
    border: none;
    border-radius: 6px;
    background: #2c3e50;
    color: white;
}
</style>

<script>
async function exportarCard(produto, ordem){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();
    pdf.text("Ordem: " + ordem, 10, 10);
    pdf.text("Produto: " + produto, 10, 20);
    pdf.save("ordem.pdf");
}

// 🆕 RANCHO
function anexarRancho(input, ordem){
    const file = input.files[0];
    if(file){
        alert("Rancho anexado para ordem " + ordem + ": " + file.name);
    }
}
</script>
</head>
<body>
"""

# 🔄 LOOP
for linha, datas in estrutura.items():
    if linha_sel != "Todas" and linha != linha_sel:
        continue

    html += f"<div class='linha'><h2>{linha}</h2>"

    for data, turnos in datas.items():
        html += f"<h3>📅 {data}</h3><div class='cards'>"

        for turno, itens in turnos.items():
            if turno_sel != "Todos" and turno != turno_sel:
                continue

            for item in itens:
                produto = item.get("Produto", "")
                ordem = item.get("Ordem", "")

                html += f"""
                <div class='card'>
                    <b>{produto}</b><br>
                    Ordem: {ordem}<br>

                    <button onclick="exportarCard('{produto}', '{ordem}')">
                        📄 PDF
                    </button>

                    <br><br>

                    <label style="font-size:12px;">📎 Rancho:</label><br>
                    <input type="file" accept="application/pdf"
                    onchange="anexarRancho(this, '{ordem}')">
                </div>
                """

        html += "</div>"

    html += "</div>"

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

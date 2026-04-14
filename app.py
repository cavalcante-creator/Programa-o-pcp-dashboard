import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date

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

estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data_original = item.get("Data", "")
    nova_data = str(item.get("Nova Data", "")).strip()
    turno = item.get("Turno", "Sem Turno")
    data_usar = nova_data if nova_data else data_original

    estrutura.setdefault(linha, {}).setdefault(data_usar, {}).setdefault(turno, []).append(item)

col1, col2, col3 = st.columns(3)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("Linha", ["Todas"] + linhas)
data_input = col2.date_input("Data", date.today())
turno_sel = col3.selectbox("Turno", ["Todos"] + turnos)

data_sel = data_input.strftime("%d/%m/%Y")

html = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

<script>
async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    let y = 10;

    pdf.setFontSize(16);
    pdf.text("ORDEM DE PRODUÇÃO", 60, y);

    y += 10;
    pdf.text("DATA: " + data, 10, y);
    pdf.text("LINHA: " + linha, 120, y);

    y += 10;
    pdf.text("PRODUTO: " + produto, 10, y);

    y += 8;
    pdf.text("ORDEM: " + ordem, 10, y);

    y += 8;
    pdf.text("TURNO: " + turno, 10, y);

    y += 8;
    pdf.text("QTDE: " + qtde, 10, y);

    y += 8;
    pdf.text("PENDENTE: " + pendente, 10, y);

    y += 10;
    pdf.text("STATUS: " + status, 10, y);

    y += 10;
    pdf.text("OBSERVAÇÕES:", 10, y);

    y += 3;
    pdf.rect(10, y, 190, 50);

    y += 55;
    pdf.text("ASSINATURA DO OPERADOR:", 10, y);

    y += 10;
    pdf.line(10, y, 100, y);

    pdf.save("ordem.pdf");
}
</script>
</head>
<body>
<div id="conteudo">
"""

for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    html += f"<h2>{linha}</h2>"

    for data, turnos in datas.items():

        if data != data_sel:
            continue

        for turno, itens in turnos.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            for item in itens:
                html += f"""
                <div style='border:1px solid #ccc;padding:10px;margin:5px'>
                <b>{item.get("Produto","")}</b><br>
                Ordem: {item.get("Ordem","")}<br>
                <button onclick="exportarCard(
                '{item.get("Produto","")}',
                '{item.get("Ordem","")}',
                '{item.get("Turno","")}',
                '{item.get("Qtde Total","")}',
                '{item.get("Qtde Pendente","")}',
                '{item.get("Status","")}',
                '{data}',
                '{linha}'
                )">Gerar PDF</button>
                </div>
                """

html += "</div></body></html>"

st.components.v1.html(html, height=800, scrolling=True)

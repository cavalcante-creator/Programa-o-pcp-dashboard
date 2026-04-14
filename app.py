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

col1, col2 = st.columns(2)

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + sorted(set(nome_linha(i["Linha"]) for i in dados_total)))

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida, format="DD/MM/YYYY")
mostrar_todas = True

data_sel = data_input.strftime("%d/%m/%Y")

html = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

<script>
let ranchos = {};

async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    pdf.setFont("helvetica","bold");
    pdf.setFontSize(16);
    pdf.text("ORDEM DE PRODUÇÃO", 60, 20);

    pdf.setFontSize(10);
    pdf.text("Produto: " + produto, 10, 40);
    pdf.text("Ordem: " + ordem, 10, 50);
    pdf.text("Turno: " + turno, 10, 60);
    pdf.text("Qtde: " + qtde, 10, 70);
    pdf.text("Pendente: " + pendente, 10, 80);
    pdf.text("Status: " + status, 10, 90);
    pdf.text("Data: " + data, 10, 100);
    pdf.text("Linha: " + linha, 10, 110);

    if(ranchos[ordem]){
        const file = ranchos[ordem];

        const reader = new FileReader();

        reader.onload = function(e){
            const img = new Image();

            img.src = e.target.result;

            img.onload = function(){
                pdf.addPage();

                const largura = 210;
                const altura = (img.height * largura) / img.width;

                pdf.addImage(img, 'PNG', 0, 0, largura, altura);

                pdf.save("ordem_producao.pdf");
            }
        };

        reader.readAsDataURL(file);

    }else{
        pdf.save("ordem_producao.pdf");
    }
}

function anexarRancho(input, ordem){
    const file = input.files[0];

    if(file){
        ranchos[ordem] = file;
        alert("Rancho anexado com sucesso!");
    }
}
</script>
</head>

<body>
"""

for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    html += f"<h2>{linha}</h2>"

    for data, turnos in datas.items():

        if not mostrar_todas and data != data_sel:
            continue

        html += f"<h3>{data}</h3>"

        for turno, itens in turnos.items():
            for item in itens:
                html += f"""
                <div style="border:1px solid #ccc;padding:10px;margin:10px;">
                {item.get("Produto")}<br>
                Ordem: {item.get("Ordem")}<br>

                <button onclick="exportarCard(
                    '{item.get("Produto")}',
                    '{item.get("Ordem")}',
                    '{item.get("Turno")}',
                    '{item.get("Qtde Total")}',
                    '{item.get("Qtde Pendente")}',
                    '{item.get("Status")}',
                    '{data}',
                    '{linha}'
                )">Gerar PDF</button>

                <br><br>

                <input type="file" accept="application/pdf"
                onchange="anexarRancho(this, '{item.get("Ordem")}')">
                </div>
                """

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

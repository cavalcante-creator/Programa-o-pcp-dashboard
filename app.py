import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date

st_autorefresh(interval=60000)
st.set_page_config(layout="wide")

# HEADER
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo { width: 200px; margin-top: 10px; }

.titulo {
    flex-grow: 1;
    text-align: center;
    font-size: 26px;
    font-weight: 600;
}

.vazio { width: 140px; }

.btn-linha {
    margin-bottom: 10px;
    padding: 8px 14px;
    background: #1f4e79;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
<img class="logo" src="https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png">
<div class="titulo">Planejamento PCP</div>
<div class="vazio"></div>
</div>
""", unsafe_allow_html=True)

# GOOGLE SHEETS
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

# FUNÇÕES
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
    if not s: return ""
    s = str(s).strip().upper()
    if "AGUARDANDO" in s: return "AGUARDANDO"
    if "PRODUÇÃO" in s: return "EM PRODUÇÃO"
    if "LIBERADA" in s: return "LIBERADA"
    return s

# ESTRUTURA
estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data_original = item.get("Data", "")
    nova_data = str(item.get("Nova Data", "")).strip()
    turno = item.get("Turno", "Sem Turno")

    data_usar = nova_data if nova_data else data_original

    estrutura.setdefault(linha, {}).setdefault(data_usar, {}).setdefault(turno, []).append(item)

# FILTROS
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida)
turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

semanas_disponiveis = sorted(set(get_semana(i.get("Data")) for i in dados_total if i.get("Data")))
semanas_sel = col4.multiselect("📆 Semanas", semanas_disponiveis)

ordem_pesquisa = col5.text_input("🔎 Buscar Ordem")
produto_pesquisa = col6.text_input("🔎 Buscar Produto")

status_lista = sorted(set(limpar_status(i.get("Status")) for i in dados_total if i.get("Status")))
status_sel = col7.selectbox("📌 Status", ["Todos"] + status_lista)

data_sel = data_input.strftime("%d/%m/%Y")

# HTML
html = """
<html>
<head>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://unpkg.com/pdf-lib/dist/pdf-lib.min.js"></script>

<script>
let arquivosRancho = {};
let dadosLinha = {};

function salvarRancho(ordem, input){
    if(input.files[0]){
        arquivosRancho[ordem] = input.files[0];
        alert("Rancho anexado!");
    }
}

async function gerarPDFSimples(produto, ordem, turno, qtde, pendente, status, data, linha){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();

    pdf.text("ORDEM: " + ordem, 10, 10);
    pdf.text("PRODUTO: " + produto, 10, 20);
    pdf.text("QTD: " + qtde, 10, 30);

    return pdf.output('arraybuffer');
}

async function exportarLinha(linha){

    const mergedPdf = await PDFLib.PDFDocument.create();

    for(let item of dadosLinha[linha]){

        const pdfBytes = await gerarPDFSimples(
            item.produto,
            item.ordem,
            item.turno,
            item.qtde,
            item.pendente,
            item.status,
            item.data,
            linha
        );

        const pdfDoc = await PDFLib.PDFDocument.load(pdfBytes);
        const pages = await mergedPdf.copyPages(pdfDoc, pdfDoc.getPageIndices());

        pages.forEach(p => mergedPdf.addPage(p));
    }

    const finalPdf = await mergedPdf.save();

    const blob = new Blob([finalPdf], { type: 'application/pdf' });
    const link = document.createElement('a');

    link.href = URL.createObjectURL(blob);
    link.download = "linha_completa.pdf";
    link.click();
}
</script>

</head>
<body>
"""

# LOOP
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = f"<div class='linha'>"
    bloco += f"<button class='btn-linha' onclick=\"exportarLinha('{linha}')\">📥 Baixar PDFs da Linha</button>"
    bloco += f"<h2>{linha}</h2>"

    html += f"<script>dadosLinha['{linha}'] = [];</script>"

    for data, turnos in datas.items():

        bloco += f"<h3>📅 {data}</h3><div class='cards'>"

        for turno, itens in turnos.items():

            for item in itens:

                produto = item.get("Produto","")
                ordem = item.get("Ordem","")

                qtde = item.get("Qtde Total","0")
                pendente = item.get("Qtde Pendente","0")
                status = item.get("Status","")

                html += f"""
                <script>
                dadosLinha['{linha}'].push({{
                    produto: "{produto}",
                    ordem: "{ordem}",
                    turno: "{turno}",
                    qtde: "{qtde}",
                    pendente: "{pendente}",
                    status: "{status}",
                    data: "{data}"
                }});
                </script>
                """

                bloco += f"""
                <div class='card'>
                <b>{produto}</b><br>
                Ordem: {ordem}<br>

                <input type="file" accept="application/pdf"
                onchange="salvarRancho('{ordem}', this)">

                </div>
                """

        bloco += "</div>"

    bloco += "</div>"

    html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

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
        valor = str(valor).replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return 0

def limpar_status(s):
    if not s:
        return ""
    s = str(s).strip().upper()

    if "AGUARDANDO" in s:
        return "AGUARDANDO"
    if "PRODUÇÃO" in s:
        return "EM PRODUÇÃO"
    if "LIBERADA" in s:
        return "LIBERADA"

    return s

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

colb1, colb2, colb3 = st.columns(3)

if colb1.button("Hoje"):
    st.session_state.data_escolhida = date.today()
    data_input = date.today()

mostrar_todas = colb2.checkbox("Mostrar todas as datas", value=True)
data_sel = data_input.strftime("%d/%m/%Y")

# 🔥 HTML + PDF
html = """
<html>
<head>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<style>
body { font-family: 'Segoe UI'; background: #f5f7fa; margin: 20px; }

.linha h2 { background: #2c3e50; color: white; padding: 10px; border-radius: 8px; }

.cards { display: flex; flex-wrap: wrap; }

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
    margin-top:8px;
    padding:6px 10px;
    border:none;
    border-radius:6px;
    background:#34495e;
    color:white;
}
</style>

<script>
function exportarCard(produto, ordem, turno, qtde, pendente, status){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    pdf.setFontSize(14);
    pdf.text("ORDEM DE PRODUÇÃO", 70, 10);

    pdf.setFontSize(9);
    pdf.text("Data: " + new Date().toLocaleDateString(), 160, 10);

    function celula(x, y, w, h, texto="") {
        pdf.rect(x, y, w, h);
        if(texto){
            pdf.text(texto, x + 2, y + 5);
        }
    }

    let y = 20;

    celula(10, y, 40, 8, "Produto");
    celula(50, y, 90, 8, produto);
    celula(140, y, 30, 8, "Ordem");
    celula(170, y, 30, 8, ordem);

    y += 8;
    celula(10, y, 40, 8, "Turno");
    celula(50, y, 40, 8, turno);
    celula(90, y, 40, 8, "Qtde");
    celula(130, y, 40, 8, qtde);

    y += 8;
    celula(10, y, 40, 8, "Pendente");
    celula(50, y, 40, 8, pendente);
    celula(90, y, 40, 8, "Status");
    celula(130, y, 40, 8, status);

    y += 15;

    let linhas = 8;
    let colunas = 6;
    let largura = 190 / colunas;
    let altura = 10;

    for(let i = 0; i < linhas; i++){
        for(let j = 0; j < colunas; j++){
            pdf.rect(10 + j * largura, y + i * altura, largura, altura);
        }
    }

    y += (linhas * altura) + 10;

    pdf.rect(10, y, 190, 50);

    pdf.setFontSize(12);
    pdf.text(produto, 15, y + 10);
    pdf.text("Ordem: " + ordem, 15, y + 20);

    pdf.setFontSize(28);
    pdf.text(qtde, 140, y + 35);

    y += 60;

    pdf.line(15, y, 80, y);
    pdf.text("Operador", 15, y + 5);

    pdf.line(110, y, 180, y);
    pdf.text("Conferente", 110, y + 5);

    pdf.save("ordem_producao.pdf");
}
</script>

</head>
<body>
"""

# 🔄 LOOP COM CORREÇÃO
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = f"<div class='linha'><h2>{linha}</h2>"
    tem_linha = False

    for data, turnos in datas.items():

        if semanas_sel and get_semana(data) not in semanas_sel:
            continue

        if not mostrar_todas and data != data_sel:
            continue

        conteudo_data = ""

        for turno, itens in turnos.items():

            if turno_sel != "Todos":
                continue

            for item in itens:

                produto = item.get("Produto", "")
                ordem = item.get("Ordem", "")
                status = item.get("Status", "")
                qtde = item.get("Qtde Total", "0")
                pendente = item.get("Qtde Pendente", "0")

                conteudo_data += f"""
                <div class='card'>
                <b>{produto}</b><br><br>

                Ordem: {ordem}<br>
                Turno: {turno}<br>
                Qtde: {qtde}<br>
                Pendente: {pendente}<br>
                Status: {status}<br>

                <button onclick="exportarCard(
                    '{produto}',
                    '{ordem}',
                    '{turno}',
                    '{qtde}',
                    '{pendente}',
                    '{status}'
                )">
                📄 Gerar PDF
                </button>

                </div>
                """

        if conteudo_data:
            tem_linha = True
            bloco += f"<h3>📅 {data}</h3><div class='cards'>{conteudo_data}</div>"

    bloco += "</div>"

    if tem_linha:
        html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

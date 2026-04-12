import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date
import json

# 🔄 Auto refresh
st_autorefresh(interval=60000)
st.set_page_config(layout="wide")

# 🎨 HEADER
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

def limpar_status(s):
    if not s:
        return ""
    s = str(s).strip().upper()
    if "AGUARDANDO" in s: return "AGUARDANDO"
    if "PRODUÇÃO" in s: return "EM PRODUÇÃO"
    if "LIBERADA" in s: return "LIBERADA"
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

ordem_pesquisa = col5.text_input("🔎 Buscar Ordem")
produto_pesquisa = col6.text_input("🔎 Buscar Produto")

colb1, colb2 = st.columns(2)

if colb1.button("Hoje"):
    st.session_state.data_escolhida = date.today()
    data_input = date.today()

mostrar_todas = colb2.checkbox("Mostrar todas as datas", value=True)

data_sel = data_input.strftime("%d/%m/%Y")

# 🔥 HTML
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

.producao { border-left: 5px solid #a9cce3; background: #f4f9fd; }
.pendente { border-left: 5px solid #f5b7b1; background: #fdf2f2; }
.finalizado { border-left: 5px solid #a9dfbf; background: #f3fbf6; }
.liberada { border-left: 5px solid #f9e79f; background: #fef9e7; }

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

// SUA FUNÇÃO ORIGINAL (mantida)
async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    let y = 10;

    pdf.text("ORDEM DE PRODUÇÃO", 70, y+10);
    y += 20;

    pdf.text("Produto: " + produto, 10, y);
    y += 10;
    pdf.text("Ordem: " + ordem, 10, y);
    y += 10;
    pdf.text("Turno: " + turno, 10, y);
    y += 10;
    pdf.text("Qtde: " + qtde, 10, y);
    y += 10;
    pdf.text("Pendente: " + pendente, 10, y);
    y += 10;
    pdf.text("Status: " + status, 10, y);
    y += 10;

    pdf.save("ordem_" + ordem + ".pdf");
}

// NOVO: BAIXAR POR LINHA
async function exportarLinha(cards){
    for (let i = 0; i < cards.length; i++) {
        const c = cards[i];

        await exportarCard(
            c.produto,
            c.ordem,
            c.turno,
            c.qtde,
            c.pendente,
            c.status,
            c.data,
            c.linha
        );

        await new Promise(r => setTimeout(r, 400));
    }
}

// RANCHO
function anexarRancho(input, ordem){
    const file = input.files[0];
    if(file){
        alert("Rancho anexado: " + ordem);
    }
}

</script>
</head>
<body>
"""

# LOOP ORIGINAL + ADIÇÃO
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = f"<div class='linha'><h2>{linha}</h2>"
    lista_cards = []

    for data, turnos in datas.items():

        if not mostrar_todas and data != data_sel:
            continue

        bloco += f"<h3>📅 {data}</h3><div class='cards'>"

        for turno, itens in turnos.items():
            for item in itens:

                produto = item.get("Produto","")
                ordem = item.get("Ordem","")
                qtde_total = item.get("Qtde Total","0")
                qtde_pendente = item.get("Qtde Pendente","0")
                status_original = item.get("Status","")

                lista_cards.append({
                    "produto": produto,
                    "ordem": ordem,
                    "turno": item.get("Turno","-"),
                    "qtde": qtde_total,
                    "pendente": qtde_pendente,
                    "status": status_original,
                    "data": data,
                    "linha": linha
                })

                bloco += f"""
                <div class='card'>
                <b>{produto}</b><br>
                Ordem: {ordem}<br>

                <button onclick="exportarCard('{produto}','{ordem}','{item.get("Turno","-")}','{qtde_total}','{qtde_pendente}','{status_original}','{data}','{linha}')">
                📄 PDF
                </button>

                <input type="file" onchange="anexarRancho(this,'{ordem}')">
                </div>
                """

        bloco += "</div>"

    # BOTÃO DA LINHA
    bloco += f"""
    <div style="margin:10px;">
        <button onclick='exportarLinha({json.dumps(lista_cards)})'>
            📥 Baixar PDFs da Linha
        </button>
    </div>
    """

    bloco += "</div>"
    html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

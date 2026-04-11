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

def limpar_status(s):
    if not s: return ""
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

# 🔥 LISTAS PARA PDF
dados_tela_js = []

# 🔥 HTML + PDF
html = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<script>

// PDF INDIVIDUAL (já existente)
"""  # (mantive tudo igual daqui pra baixo, só adicionei funções novas)

html += """

async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    let y = 10;

    function campo(x,y,w,h,t,v){
        pdf.setFontSize(8);
        pdf.setFont("helvetica","bold");
        pdf.text(t,x,y-1);
        pdf.rect(x,y,w,h);
        pdf.setFont("helvetica","normal");
        pdf.setFontSize(10);
        let linhas = pdf.splitTextToSize(v, w - 4);
        pdf.text(linhas, x+2, y+6);
    }

    campo(10,y,120,12,"PRODUTO",produto);
    campo(130,y,70,12,"ORDEM",ordem);

    y+=16;

    campo(10,y,60,12,"TURNO",turno);
    campo(70,y,60,12,"QTDE",qtde);
    campo(130,y,70,12,"PENDENTE",pendente);

    y+=16;

    campo(10,y,120,12,"STATUS",status);
    campo(130,y,70,12,"OPERADOR","");

    y+=16;

    campo(10,y,120,12,"RANCHO","");

    pdf.save("ordem.pdf");
}

// PDF LINHA
async function exportarLinha(dados, linha){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();

    let y = 10;

    dados.forEach(item=>{
        pdf.text(item.produto + " - " + item.ordem, 10, y);
        y+=6;
    });

    pdf.save("linha_"+linha+".pdf");
}

// PDF TELA
async function exportarTela(dados){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();

    let y = 10;

    dados.forEach(item=>{
        pdf.text(item.produto + " - " + item.ordem, 10, y);
        y+=6;
    });

    pdf.save("pcp_filtrado.pdf");
}

// RANCHO
function anexarRancho(input, ordem){
    const file = input.files[0];
    if(file){
        alert("Rancho anexado: " + file.name);
    }
}

</script>
</head>
<body>
"""

# 🔘 BOTÃO TELA
st.markdown(f"""
<button onclick='exportarTela({json.dumps(dados_tela_js)})'
style="padding:10px; background:#117a65; color:white; border:none; border-radius:8px;">
📥 Baixar PDF da Tela
</button>
""", unsafe_allow_html=True)

# 🔄 LOOP NORMAL (mantido)
for linha, datas in estrutura.items():

    bloco = f"<div><h2>{linha}</h2>"
    dados_linha_js = []

    for data, turnos in datas.items():
        for turno, itens in turnos.items():
            for item in itens:

                produto = item.get("Produto","")
                ordem = item.get("Ordem","")

                dados_linha_js.append({
                    "produto": produto,
                    "ordem": ordem
                })

                dados_tela_js.append({
                    "produto": produto,
                    "ordem": ordem
                })

                bloco += f"""
                <div>
                {produto} - {ordem}

                <button onclick="exportarCard('{produto}','{ordem}','{turno}','0','0','-','{data}','{linha}')">
                PDF
                </button>

                <input type="file" onchange="anexarRancho(this,'{ordem}')">
                </div>
                """

    bloco += f"""
    <button onclick='exportarLinha({json.dumps(dados_linha_js)}, "{linha}")'>
    📥 Linha
    </button>
    </div>
    """

    html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

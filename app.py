import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date

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

def limpar_status(s):
    if not s: return ""
    s = str(s).strip().upper()
    if "AGUARDANDO" in s: return "AGUARDANDO"
    if "PRODUÇÃO" in s: return "EM PRODUÇÃO"
    if "LIBERADA" in s: return "LIBERADA"
    return s

def to_float(valor):
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except:
        return 0

# 🔧 ORGANIZAÇÃO
estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data = item.get("Nova Data") or item.get("Data")
    turno = item.get("Turno","Sem Turno")

    estrutura.setdefault(linha, {}).setdefault(data, {}).setdefault(turno, []).append(item)

# 🔽 FILTROS
linha_sel = st.selectbox("🏭 Linha", ["Todas"] + sorted(estrutura.keys()))

# 🔥 HTML
html = """
<html>
<head>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<style>
body { font-family: 'Segoe UI'; background: #f5f7fa; }
.linha h2 { background:#2c3e50;color:white;padding:10px;border-radius:8px; }
.cards { display:flex;flex-wrap:wrap; }
.card { width:260px;margin:8px;padding:12px;border-radius:12px;background:white;
box-shadow:0 4px 12px rgba(0,0,0,0.06); }
</style>

<script>
function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF();

    let y = 15;

    pdf.setFont("helvetica","bold");
    pdf.setFontSize(16);
    pdf.text("ORDEM DE PRODUÇÃO", 60, y);

    pdf.setFontSize(12);
    pdf.text("DATA: " + data, 10, y + 8);
    pdf.text("LINHA: " + linha, 120, y + 8);

    y += 18;

    function campo(x,y,w,h,t,v){
        pdf.setFontSize(8);
        pdf.setFont("helvetica","bold");
        pdf.text(t, x, y-1);
        pdf.rect(x,y,w,h);
        pdf.setFont("helvetica","normal");
        pdf.text(v, x+2, y+6);
    }

    campo(10,y,120,12,"PRODUTO",produto);
    campo(130,y,70,12,"ORDEM",ordem);

    y+=16;

    campo(10,y,60,12,"TURNO",turno);
    campo(70,y,60,12,"QUANTIDADE PROGRAMADA",qtde);
    campo(130,y,70,12,"QUANTIDADE PENDENTE",pendente);

    y+=16;

    campo(10,y,190,12,"STATUS",status);

    // 📊 GRADE NOVA
    y+=20;

    let colunas = ["HORA INICIO","HORA FIM","N PALLETS","SACOS (UN)","RASGADOS","PARADAS"];
    let largura = 190/colunas.length;
    let altura = 10;

    pdf.setFont("helvetica","bold");

    colunas.forEach((c,i)=>{
        pdf.rect(10+i*largura,y,largura,altura);
        pdf.text(c,10+i*largura+2,y+6);
    });

    pdf.setFont("helvetica","normal");

    y+=altura;

    for(let i=0;i<8;i++){
        for(let j=0;j<colunas.length;j++){
            pdf.rect(10+j*largura,y,largura,altura);
        }
        y+=altura;
    }

    pdf.save("ordem.pdf");
}
</script>

</head>
<body>
"""

# 🔄 LOOP
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = f"<div class='linha'><h2>{linha}</h2>"
    tem = False

    for data, turnos in datas.items():

        conteudo = ""

        for turno, itens in turnos.items():

            for item in itens:

                produto = item.get("Produto","")
                ordem = item.get("Ordem","")
                qtde = item.get("Qtde Total","0")
                pendente = item.get("Qtde Pendente","0")
                status = item.get("Status","")

                conteudo += f"""
                <div class='card'>
                <b>{produto}</b><br>
                Ordem: {ordem}<br>
                Turno: {turno}<br>
                Qtde: {qtde}<br>
                Pendente: {pendente}<br>
                Status: {status}<br>

                <button onclick="exportarCard(
                '{produto}','{ordem}','{turno}','{qtde}',
                '{pendente}','{status}','{data}','{linha}')">
                📄 PDF
                </button>

                </div>
                """

        if conteudo:
            tem=True
            bloco+=f"<h3>📅 {data}</h3><div class='cards'>{conteudo}</div>"

    bloco+="</div>"

    if tem:
        html+=bloco

html+="</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

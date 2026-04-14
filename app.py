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

# 🔥 HTML + PDF
html = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

<script>

let ranchos = {};

// 🔹 EXPORTAR PÁGINA
async function exportarPagina(){
    const { jsPDF } = window.jspdf;
    const elemento = document.getElementById("conteudo");
    const canvas = await html2canvas(elemento, { scale: 2 });
    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF('p','mm','a4');
    const largura = 210;
    const altura = (canvas.height * largura) / canvas.width;

    pdf.addImage(imgData, 'PNG', 0, 0, largura, altura);
    pdf.save("pagina_completa.pdf");
}

// 🔹 EXPORTAR ORDEM
async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    let y = 10;

    const logoUrl = "https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png";

    try {
        const img = await fetch(logoUrl);
        const blob = await img.blob();
        const reader = new FileReader();

        await new Promise(resolve => {
            reader.onloadend = resolve;
            reader.readAsDataURL(blob);
        });

        const base64 = reader.result;
        const props = pdf.getImageProperties(base64);

        const largura = 30;
        const altura = (props.height * largura) / props.width;

        pdf.addImage(base64, 'PNG', 10, y, largura, altura);
    } catch(e){}

    pdf.setFont("helvetica","bold");
    pdf.setFontSize(16);
    pdf.text("ORDEM DE PRODUÇÃO", 70, y + 10);

    y += 20;

    pdf.setFillColor(44,62,80);
    pdf.rect(10, y, 190, 8, 'F');

    pdf.setTextColor(255,255,255);
    pdf.text("DATA: " + data, 15, y + 5.5);
    pdf.text("LINHA: " + linha, 120, y + 5.5);

    pdf.setTextColor(0,0,0);
    y += 18;

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
    campo(70,y,60,12,"QUANTIDADE PROGRAMADA",qtde);
    campo(130,y,70,12,"QUANTIDADE PENDENTE",pendente);
    y+=16;

    campo(10,y,120,12,"STATUS",status);
    campo(130,y,70,12,"OPERADOR","");
    y+=16;

    campo(10,y,120,12,"RANCHO","");
    y+=20;

    let colunas = ["HORA INICIO","HORA FIM","N PALLETS","SACOS (UN)","RASGADOS","PARADAS"];
    let larguraTabela = 190/colunas.length;
    let alturaLinha = 8;

    pdf.setFont("helvetica","bold");

    colunas.forEach((c,i)=>{
        pdf.rect(10+i*larguraTabela,y,larguraTabela,alturaLinha);
        pdf.text(c,10+i*larguraTabela+1,y+5);
    });

    pdf.setFont("helvetica","normal");
    y+=alturaLinha;

    const limite = 180;

    while(y < limite){
        for(let j=0;j<colunas.length;j++){
            pdf.rect(10+j*larguraTabela,y,larguraTabela,alturaLinha);
        }
        y+=alturaLinha;
    }

    y += 5;
    pdf.setFont("helvetica","bold");
    pdf.text("OBSERVAÇÕES:", 10, y);

    y += 3;
    pdf.rect(10, y, 190, 50);

    y += 55;

    pdf.setFont("helvetica","bold");
    pdf.text("ASSINATURA DO OPERADOR:", 10, y);

    y += 10;
    pdf.line(10, y, 100, y);

    pdf.save("ordem_producao.pdf");
}

// 🔹 ANEXAR RANCHO
function anexarRancho(input, ordem){
    const file = input.files[0];
    if(file){
        const reader = new FileReader();
        reader.onload = function(e){
            ranchos[ordem] = {
                nome: file.name,
                arquivo: e.target.result
            };
            alert("PDF do rancho anexado: " + file.name);
        };
        reader.readAsDataURL(file);
    }
}

</script>

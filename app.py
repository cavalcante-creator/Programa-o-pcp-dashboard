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

# 🆕 LISTA PARA PDF DA TELA
dados_tela_js = []

# 🔘 BOTÃO PDF TELA
st.markdown(f"""
<button onclick='exportarTela({json.dumps(dados_tela_js)})'
style="padding:10px; background:#117a65; color:white; border:none; border-radius:8px;">
📥 Baixar PDF da Tela Filtrada
</button>
""", unsafe_allow_html=True)

# 🔥 HTML + PDF
html = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<script>

// 🆕 PDF TELA
async function exportarTela(dados){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    let y = 10;

    pdf.setFont("helvetica","bold");
    pdf.setFontSize(16);
    pdf.text("PLANEJAMENTO PCP", 20, y);

    y += 10;

    for(let i = 0; i < dados.length; i++){

        let item = dados[i];

        if(y > 270){
            pdf.addPage();
            y = 10;
        }

        pdf.setFontSize(10);

        pdf.text("Linha: " + item.linha, 10, y); y+=5;
        pdf.text("Data: " + item.data, 10, y); y+=5;
        pdf.text("Produto: " + item.produto, 10, y); y+=5;
        pdf.text("Ordem: " + item.ordem, 10, y); y+=5;
        pdf.text("Turno: " + item.turno, 10, y); y+=5;
        pdf.text("Qtde: " + item.qtde, 10, y); y+=5;
        pdf.text("Pendente: " + item.pendente, 10, y); y+=5;

        y += 5;
        pdf.line(10, y, 200, y);
        y += 5;
    }

    pdf.save("pcp_filtrado.pdf");
}

</script>
"""

# 🔄 LOOP (SEU ORIGINAL + 1 LINHA ADICIONADA)
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = f"<div class='linha'><h2>{linha}</h2>"
    tem_linha = False

    for data, turnos in datas.items():

        if not mostrar_todas and data != data_sel:
            continue

        itens_filtrados = []

        for turno, itens in turnos.items():

            if turno_sel != "Todos":
                continue

            for item in itens:

                ordem = item.get("Ordem", "")
                produto = item.get("Produto", "")
                status_original = item.get("Status", "")

                if ordem_pesquisa and ordem_pesquisa not in ordem:
                    continue

                if produto_pesquisa and produto_pesquisa.lower() not in produto.lower():
                    continue

                # 🆕 AQUI (única adição no loop)
                dados_tela_js.append({
                    "linha": linha,
                    "data": data,
                    "produto": produto,
                    "ordem": ordem,
                    "turno": item.get("Turno","-"),
                    "qtde": str(item.get("Qtde Total","0")),
                    "pendente": str(item.get("Qtde Pendente","0"))
                })

                itens_filtrados.append(item)

        if not itens_filtrados:
            continue

        tem_linha = True
        bloco += f"<h3>📅 {data}</h3><div class='cards'>"

        for item in itens_filtrados:

            produto = item.get("Produto", "")
            ordem = item.get("Ordem", "")
            status_original = item.get("Status", "")

            qtde_total = item.get("Qtde Total", "0")
            qtde_pendente = item.get("Qtde Pendente", "0")

            total = to_float(qtde_total)
            pendente = to_float(qtde_pendente)
            status_lower = status_original.lower()

            if "liberada" in status_lower:
                classe = "liberada"
            elif pendente == 0:
                classe = "finalizado"
            elif pendente < total:
                classe = "producao"
            else:
                classe = "pendente"

            bloco += f"""
            <div class='card {classe}'>
            <b>{produto}</b><br>
            Ordem: {ordem}<br>
            Turno: {item.get("Turno","-")}<br>
            Qtde: {qtde_total}<br>
            Pendente: {qtde_pendente}<br>
            Status: {status_original}<br>
            </div>
            """

        bloco += "</div>"

    bloco += "</div>"

    if tem_linha:
        html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

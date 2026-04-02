import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date

# 🔄 Auto refresh
st_autorefresh(interval=60000)

st.set_page_config(layout="wide")

# 🎨 ESTILO + HEADER
st.markdown("""
<style>
.block-container { padding-top: 0.5rem; }

.header {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.logo { width: 180px; }

.titulo {
    flex-grow: 1;
    text-align: center;
    font-size: 28px;
    font-weight: 600;
}

/* DIA */
.dia {
    margin-bottom: 30px;
}

.dia h2 {
    background: #2c3e50;
    color: white;
    padding: 10px;
    border-radius: 8px;
}

/* 🔥 BLOCO LINHA */
.linha {
    margin-top: 15px;
    padding: 12px;
    background: #ffffff;
    border-radius: 10px;
    border: 1px solid #dcdcdc;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.05);
}

.linha h4 {
    margin-bottom: 10px;
    font-size: 16px;
    color: #2c3e50;
    border-left: 5px solid #2c3e50;
    padding-left: 8px;
}

/* CARDS */
.cards {
    display: flex;
    flex-wrap: wrap;
}

.card {
    width: 230px;
    padding: 10px;
    margin: 6px;
    border-radius: 10px;
    background: #fdfdfd;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
    border-left: 5px solid transparent;
    font-size: 13px;
}

.falta { border-left: 5px solid #e74c3c; }
.ok { border-left: 5px solid #2ecc71; }
.sobra { border-left: 5px solid #f1c40f; }
.atrasado { border-left: 5px solid #c0392b; }

/* PRINT */
@media print {
    body { background: white; }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <img class="logo" src="https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png">
    <div class="titulo">Planejamento PCP</div>
    <div style="width:140px;"></div>
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

# 🔧 ESTRUTURA
estrutura = {}

for item in dados_total:
    data = item.get("Data", "")
    linha = nome_linha(item["Linha"])
    turno = item.get("Turno", "Sem Turno")

    estrutura.setdefault(data, {}).setdefault(linha, {}).setdefault(turno, []).append(item)

# 🔽 FILTROS
col1, col2, col3, col4 = st.columns(4)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_total))
turnos = sorted(set(i["Turno"] for i in dados_total if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida, format="DD/MM/YYYY")

turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

semanas_disponiveis = sorted(set(get_semana(i.get("Data")) for i in dados_total if i.get("Data")))
semanas_sel = col4.multiselect("📆 Semanas", semanas_disponiveis)

mostrar_todas = st.checkbox("Mostrar todas as datas", value=True)

data_sel = data_input.strftime("%d/%m/%Y")

# 🔥 HTML FINAL
html = "<html><body>"

for data, linhas_dict in sorted(estrutura.items()):

    if not mostrar_todas and data != data_sel:
        continue

    if semanas_sel and get_semana(data) not in semanas_sel:
        continue

    bloco_dia = f"<div class='dia'><h2>📅 {data}</h2>"
    tem_conteudo = False

    for linha, turnos_dict in linhas_dict.items():

        if linha_sel != "Todas" and linha != linha_sel:
            continue

        cards_html = ""
        tem_linha = False

        for turno, itens in turnos_dict.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            for item in itens:
                tem_conteudo = True
                tem_linha = True

                status = item.get("Status", "").lower()

                classe = "ok"
                if "falta" in status:
                    classe = "falta"
                elif "sobra" in status:
                    classe = "sobra"
                elif "atras" in status:
                    classe = "atrasado"

                cards_html += f"""
                <div class='card {classe}'>
                    <b>{item.get("Produto")}</b><br>
                    Ordem: {item.get("Ordem")}<br>
                    Qtde: {item.get("Qtde Total")}
                </div>
                """

        if tem_linha:
            bloco_dia += f"""
            <div class='linha'>
                <h4>{linha}</h4>
                <div class='cards'>
                    {cards_html}
                </div>
            </div>
            """

    bloco_dia += "</div>"

    if tem_conteudo:
        html += bloco_dia

html += "</body></html>"

# 🚀 EXIBIR
st.components.v1.html(html, height=2500, scrolling=True)

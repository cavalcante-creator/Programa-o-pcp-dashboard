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

.card {
    width: 260px;
    padding: 12px;
    margin: 8px;
    border-radius: 12px;
    background: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    border-left: 5px solid transparent;
}

.finalizado { border-left: 5px solid #2ecc71; }
.producao { border-left: 5px solid #3498db; }
.pendente { border-left: 5px solid #e74c3c; }
.reprogramado { border-left: 5px solid #9b59b6; }

.cards { display: flex; flex-wrap: wrap; }

.linha h2 { background: #2c3e50; color: white; padding: 10px; border-radius: 8px; }
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

def to_float(valor):
    try:
        valor = str(valor).replace(".", "").replace(",", ".")
        return float(valor)
    except:
        return 0

# 🔁 DUPLICAÇÃO POR NOVA DATA
dados_expandido = []

for item in dados_total:
    nova_data = str(item.get("Nova Data", "")).strip()

    # sempre adiciona na data original
    dados_expandido.append(item.copy())

    # se tiver nova data → cria uma cópia com a nova data
    if nova_data:
        novo_item = item.copy()
        novo_item["Data"] = nova_data
        novo_item["Reprogramado"] = "Sim"
        dados_expandido.append(novo_item)

# 🔧 ORGANIZAÇÃO
estrutura = {}

for item in dados_expandido:
    linha = nome_linha(item["Linha"])
    data = item.get("Data", "")
    turno = item.get("Turno", "Sem Turno")

    estrutura.setdefault(linha, {}).setdefault(data, {}).setdefault(turno, []).append(item)

# 🔽 FILTROS
col1, col2, col3, col4, col5 = st.columns(5)

linhas = sorted(set(nome_linha(i["Linha"]) for i in dados_expandido))
turnos = sorted(set(i["Turno"] for i in dados_expandido if i["Turno"]))

linha_sel = col1.selectbox("🏭 Linha", ["Todas"] + linhas)

if "data_escolhida" not in st.session_state:
    st.session_state.data_escolhida = date.today()

data_input = col2.date_input("📅 Data", st.session_state.data_escolhida, format="DD/MM/YYYY")
turno_sel = col3.selectbox("⏱ Turno", ["Todos"] + turnos)

ordem_pesquisa = col5.text_input("🔎 Buscar Ordem")

mostrar_todas = col4.checkbox("Mostrar todas as datas", value=True)

data_sel = data_input.strftime("%d/%m/%Y")

# 🔥 HTML
html = "<html><body>"

# 🔄 LOOP
for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = f"<div class='linha'><h2>{linha}</h2>"
    tem = False

    for data, turnos in datas.items():

        if not mostrar_todas and data != data_sel:
            continue

        bloco += f"<h3>📅 {data}</h3>"
        bloco += "<div class='cards'>"

        for turno, itens in turnos.items():

            if turno_sel != "Todos":
                continue

            for item in itens:

                ordem = item.get("Ordem", "")

                if ordem_pesquisa and ordem_pesquisa not in ordem:
                    continue

                tem = True

                qtde_total = item.get("Qtde Total", "0")
                qtde_pendente = item.get("Qtde Pendente", "0")
                nova_data = str(item.get("Nova Data", "")).strip()
                reprogramado = item.get("Reprogramado", "")

                total = to_float(qtde_total)
                pendente = to_float(qtde_pendente)

                # 🎨 cor
                if nova_data:
                    classe = "reprogramado"
                elif pendente == 0:
                    classe = "finalizado"
                elif pendente < total:
                    classe = "producao"
                else:
                    classe = "pendente"

                bloco += f"""
                <div class='card {classe}'>
                <b>{item.get("Produto")}</b><br>
                Ordem: {ordem}<br>
                Turno: {item.get("Turno","-")}<br>
                Qtde: {qtde_total}<br>
                Status: {item.get("Status","-")}<br>
                Pendente: {qtde_pendente}<br>
                {"🔁 Nova Data: " + nova_data + "<br>" if nova_data else ""}
                </div>
                """

        bloco += "</div>"

    bloco += "</div>"

    if tem:
        html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

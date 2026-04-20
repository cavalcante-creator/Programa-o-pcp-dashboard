import streamlit as st
from streamlit_autorefresh import st_autorefresh
import requests
import csv
from io import StringIO
from datetime import datetime, date
import json

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycby0sYky_AQVQN7NMv0MK55UngaBm7ayey1mJB37BE7lB6rNjmUvUJ68FD0-qsPe-vgT/exec"

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

def esc(valor):
    return str(valor).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace("\n", " ").replace("\r", "")

def carregar_ranchos():
    try:
        r = requests.get(
            APPS_SCRIPT_URL,
            params={"acao": "listar", "_ts": int(datetime.now().timestamp())},
            timeout=15
        )
        r.raise_for_status()
        data = r.json()
        if not isinstance(data, dict):
            return {}
        return {str(k).strip(): v for k, v in data.items()}
    except:
        return {}

ranchos_atuais = carregar_ranchos()

sheet_id = "1eQHvLVw-WLsA4UruaM6GThcy0dgb5ONNAn8AZ_KwBuU"

abas = [
    "BASE_LINHA_1","BASE_LINHA_2","BASE_LINHA_3",
    "BASE_AREA_LIQUIDA",
    "BASE_REJUNTE_MAQUINA_1","BASE_REJUNTE_MAQUINA_2","BASE_REJUNTE_MAQUINA_3"
]

dados_total = []

for aba in abas:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={aba}"
    response = requests.get(url, timeout=20)
    f = StringIO(response.text)
    reader = csv.DictReader(f)
    for linha in reader:
        linha["Linha"] = aba
        dados_total.append(linha)

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

estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data_original = item.get("Data", "")
    nova_data = str(item.get("Nova Data", "")).strip()
    turno = item.get("Turno", "Sem Turno")
    data_usar = nova_data if nova_data else data_original
    estrutura.setdefault(linha, {}).setdefault(data_usar, {}).setdefault(turno, []).append(item)

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

ranchos_meta_json = json.dumps({str(k).strip(): {"numero": v.get("numero",""), "nome": v.get("nome","")} for k, v in ranchos_atuais.items()})
ranchos_b64_json  = json.dumps({str(k).strip(): v.get("base64","") for k, v in ranchos_atuais.items()})

html_head = """
<html>
<head>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js"></script>

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
.reprogramado { border-left: 5px solid #d7bde2; background: #f8f4fb; }
.liberada { border-left: 5px solid #f9e79f; background: #fef9e7; }

button {
    margin-top: 8px;
    padding: 6px 10px;
    border: none;
    border-radius: 6px;
    background: #2c3e50;
    color: white;
    cursor: pointer;
}

.upload-label {
    display: inline-block;
    margin-top: 8px;
    padding: 6px 10px;
    border-radius: 6px;
    background: #5d6d7e;
    color: white;
    font-size: 12px;
    cursor: pointer;
}

.upload-label input { display: none; }
</style>

<script>
const RANCHOS_META = __RANCHOS_META__;
const RANCHOS_B64  = __RANCHOS_B64__;
const APPS_SCRIPT_URL = "__APPS_SCRIPT_URL__";

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

async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){
    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');
    let y = 10;

    const logoUrl = "https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png";
    try {
        const img = await fetch(logoUrl);
        const blob = await img.blob();
        const reader = new FileReader();
        await new Promise(resolve => { reader.onloadend = resolve; reader.readAsDataURL(blob); });
        const base64 = reader.result;
        const props = pdf.getImageProperties(base64);
        const larg = 30;
        const alt = (props.height * larg) / props.width;
        pdf.addImage(base64, 'PNG', 10, y, larg, alt);
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
        pdf.setFontSize(8); pdf.setFont("helvetica","bold");
        pdf.text(t,x,y-1); pdf.rect(x,y,w,h);
        pdf.setFont("helvetica","normal"); pdf.setFontSize(10);
        let linhas = pdf.splitTextToSize(String(v), w - 4);
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

    const meta = RANCHOS_META[ordem];
    const numeroRancho = meta ? meta.numero : "";
    campo(10, y, 120, 12, "RANCHO", numeroRancho);
    y+=20;

    let colunas;
    if(linha.toUpperCase().includes("AREA LIQUIDA")){
        colunas = ["HORA INICIO","HORA FIM","N PALLETS","FD","RASGADOS","PARADAS"];
    } else {
        colunas = ["HORA INICIO","HORA FIM","N PALLETS","SACOS (UN)","RASGADOS","PARADAS"];
    }

    let larguraTabela = 190/colunas.length;
    let alturaLinha = 8;
    pdf.setFont("helvetica","bold");
    colunas.forEach((c,i)=>{
        pdf.rect(10+i*larguraTabela,y,larguraTabela,alturaLinha);
        pdf.text(c,10+i*larguraTabela+1,y+5);
    });
    pdf.setFont("helvetica","normal");
    y+=alturaLinha;
    const limite = 210;
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
    pdf.rect(10, y, 190, 30);
    y += 45;
    pdf.setFont("helvetica","bold");
    pdf.text("ASSINATURA DO OPERADOR:", 10, y);
    y += 10;
    pdf.line(10, y, 100, y);
    pdf.setFont("helvetica","normal");
    pdf.setFontSize(8);
    pdf.text("Nome / Assinatura", 10, y + 4);

    const link = RANCHOS_META[ordem]?.link;
window.open(link, "_blank");
    if(b64Rancho){
        try {
            const { PDFDocument } = PDFLib;
            const pdfPrincipalBytes = pdf.output('arraybuffer');
            const binaryStr = atob(b64Rancho);
            const ranchoBytes = new Uint8Array(binaryStr.length);
            for(let i = 0; i < binaryStr.length; i++){
                ranchoBytes[i] = binaryStr.charCodeAt(i);
            }
            const docFinal   = await PDFDocument.load(pdfPrincipalBytes);
            const docRancho  = await PDFDocument.load(ranchoBytes);
            const paginas    = await docFinal.copyPages(docRancho, docRancho.getPageIndices());
            paginas.forEach(p => docFinal.addPage(p));

            const bytesFinais = await docFinal.save();
            const blob = new Blob([bytesFinais], { type: 'application/pdf' });
            const url  = URL.createObjectURL(blob);
            const a    = document.createElement('a');
            a.href     = url;
            a.download = 'ordem_producao.pdf';
            a.click();
            URL.revokeObjectURL(url);
            return;
        } catch(e){
            console.warn("Erro ao mesclar rancho:", e);
        }
    }

    pdf.save("ordem_producao.pdf");
}

function verRancho(ordem){
    const b64 = RANCHOS_B64[ordem];
    if(!b64){
        alert("❌ Nenhum rancho anexado para essa ordem");
        return;
    }
    const dataUrl = "data:application/pdf;base64," + b64;
    const novaAba = window.open("", "_blank");
    novaAba.document.write('<html><head><title>Rancho</title></head><body style="margin:0"><iframe src="' + dataUrl + '" width="100%" height="100%" style="border:none;"></iframe></body></html>');
    novaAba.document.close();
}

function anexarRancho(input, ordem){
    const file = input.files[0];
    if(!file) return;

    const statusEl = document.getElementById("status_" + ordem);
    if(statusEl){
        statusEl.innerHTML = "⏳ Enviando...";
        statusEl.style.color = "orange";
    }

    const reader = new FileReader();
    reader.onload = function(e){
        const b64 = e.target.result.split(",")[1];

        let numeroRancho = "";
        try {
            const decoded = atob(b64);
            const match = decoded.match(/rancho\\s*\\(?\\s*(\\d+)/i);
            if(match) numeroRancho = match[1];
        } catch(err){}

        if(!numeroRancho){
            numeroRancho = prompt("Número do rancho não identificado. Digite manualmente:") || "Não informado";
        }

        const iframe = document.getElementById("upload_target");
        const form = document.createElement("form");
        form.method = "POST";
        form.action = APPS_SCRIPT_URL;
        form.target = "upload_target";
        form.style.display = "none";

        function addField(name, value){
            const input = document.createElement("input");
            input.type = "hidden";
            input.name = name;
            input.value = value;
            form.appendChild(input);
        }

        addField("acao", "salvar");
        addField("ordem", ordem);
        addField("numero", numeroRancho);
        addField("nome", file.name);
        addField("b64", b64);

        document.body.appendChild(form);
        form.submit();

        setTimeout(function(){
            RANCHOS_META[ordem] = { numero: numeroRancho, nome: file.name };
            RANCHOS_B64[ordem] = b64;
            if(statusEl){
                statusEl.innerHTML = "✅ Rancho: " + numeroRancho;
                statusEl.style.color = "green";
            }
            form.remove();
        }, 1500);
    };

    reader.readAsDataURL(file);
}

window.onload = function(){
    document.querySelectorAll("[id^='status_']").forEach(el => {
        let ordem = el.id.replace("status_", "");
        if(RANCHOS_META[ordem]){
            el.innerHTML = "✅ Rancho: " + RANCHOS_META[ordem].numero;
            el.style.color = "green";
        } else {
            el.innerHTML = "❌ Nenhum rancho";
            el.style.color = "red";
        }
    });
};
</script>
</head>

<body>
<iframe name="upload_target" id="upload_target" style="display:none;"></iframe>

<div style="margin-bottom:15px;">
    <button onclick="exportarPagina()">📥 Baixar Página Completa</button>
</div>
<div id="conteudo">
"""

html_head = html_head.replace("__RANCHOS_META__", ranchos_meta_json)
html_head = html_head.replace("__RANCHOS_B64__",  ranchos_b64_json)
html_head = html_head.replace("__APPS_SCRIPT_URL__", APPS_SCRIPT_URL)

html = html_head

for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco = "<div class='linha'><h2>" + linha + "</h2>"
    tem_linha = False

    for data, turnos in datas.items():

        if not mostrar_todas and data != data_sel:
            continue

        itens_filtrados = []

        for turno, itens in turnos.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            for item in itens:
                ordem = str(item.get("Ordem", "")).strip()
                produto = item.get("Produto", "")
                status_original = item.get("Status", "")
                status_limpo = limpar_status(status_original)

                if status_sel != "Todos" and status_limpo != status_sel:
                    continue
                if ordem_pesquisa and ordem_pesquisa not in ordem:
                    continue
                if produto_pesquisa and produto_pesquisa.lower() not in produto.lower():
                    continue
                if semanas_sel:
                    semana_item = get_semana(item.get("Data", ""))
                    if semana_item not in semanas_sel:
                        continue

                item["Ordem"] = ordem
                itens_filtrados.append(item)

        if not itens_filtrados:
            continue

        tem_linha = True
        bloco += "<h3>📅 " + data + "</h3><div class='cards'>"

        for item in itens_filtrados:
            produto = item.get("Produto", "")
            ordem = str(item.get("Ordem", "")).strip()
            status_original = item.get("Status", "")
            qtde_total = item.get("Qtde Total", "0")
            qtde_pendente = item.get("Qtde Pendente", "0")
            turno_item = item.get("Turno", "-")

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

            tem_rancho = ordem in ranchos_atuais
            if tem_rancho:
                status_rancho_html = '<span style="color:green;font-size:11px;">✅ Rancho: ' + esc(ranchos_atuais[ordem].get("numero","")) + '</span>'
            else:
                status_rancho_html = '<span style="color:red;font-size:11px;">❌ Nenhum rancho</span>'

            p_esc  = esc(produto)
            o_esc  = esc(ordem)
            t_esc  = esc(turno_item)
            qt_esc = esc(qtde_total)
            qp_esc = esc(qtde_pendente)
            s_esc  = esc(status_original)
            d_esc  = esc(data)
            l_esc  = esc(linha)

            bloco += (
                "<div class='card " + classe + "'>"
                "<b>" + produto + "</b><br>"
                "Ordem: " + ordem + "<br>"
                "Turno: " + turno_item + "<br>"
                "Qtde: " + qtde_total + "<br>"
                "Pendente: " + qtde_pendente + "<br>"
                "Status: " + status_original + "<br>"
                "<button onclick=\"exportarCard('"
                + p_esc + "','" + o_esc + "','" + t_esc + "','"
                + qt_esc + "','" + qp_esc + "','" + s_esc + "','"
                + d_esc + "','" + l_esc + "')\">📄 Gerar PDF</button>"
                "<br>"
                "<label class='upload-label'>📎 Anexar Rancho"
                "<input type='file' accept='application/pdf' onchange=\"anexarRancho(this,'" + o_esc + "')\"></label>"
                " <button onclick=\"verRancho('" + o_esc + "')\">👁 Ver Rancho</button>"
                "<div id='status_" + o_esc + "' style='font-size:11px;margin-top:4px;'>" + status_rancho_html + "</div>"
                "</div>"
            )

        bloco += "</div>"
    bloco += "</div>"

    if tem_linha:
        html += bloco

html += "</div></body></html>"

st.components.v1.html(html, height=900, scrolling=True)

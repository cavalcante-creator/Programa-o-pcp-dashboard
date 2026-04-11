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

def nome_linha(linha):
    return linha.replace("BASE_", "").replace("_", " ")

def to_float(valor):
    try:
        return float(str(valor).replace(".", "").replace(",", "."))
    except:
        return 0

estrutura = {}

for item in dados_total:
    linha = nome_linha(item["Linha"])
    data = item.get("Nova Data") or item.get("Data")
    turno = item.get("Turno", "Sem Turno")

    estrutura.setdefault(linha, {}).setdefault(data, {}).setdefault(turno, []).append(item)

# HTML + JS
html = """
<html>
<head>

<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://unpkg.com/pdf-lib/dist/pdf-lib.min.js"></script>

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

.producao { border-left: 5px solid #a9cce3; background: #f4f9fd; }
.pendente { border-left: 5px solid #f5b7b1; background: #fdf2f2; }
.finalizado { border-left: 5px solid #a9dfbf; background: #f3fbf6; }
.liberada { border-left: 5px solid #f9e79f; background: #fef9e7; }

button {
    margin-top: 6px;
    padding: 6px 10px;
    border-radius: 6px;
    background: #2c3e50;
    color: white;
    border: none;
}
</style>

<script>

let arquivosRancho = {};

function salvarRancho(ordem, input){
    const file = input.files[0];
    if(file){
        arquivosRancho[ordem] = file;
        alert("Rancho anexado!");
    }
}

async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    let y = 10;

    // LOGO
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
        pdf.text(t,x,y-1);
        pdf.rect(x,y,w,h);
        pdf.setFontSize(10);
        pdf.text(v,x+2,y+6);
    }

    campo(10,y,120,12,"PRODUTO",produto);
    campo(130,y,70,12,"ORDEM",ordem);

    y+=16;

    campo(10,y,60,12,"TURNO",turno);
    campo(70,y,60,12,"QUANTIDADE PROGRAMADA",qtde);
    campo(130,y,70,12,"QUANTIDADE PENDENTE",pendente);

    y+=16;

    campo(10,y,110,12,"STATUS",status);
    campo(120,y,80,12,"OPERADOR","");

    y+=20;

    let colunas = ["HORA INICIO","HORA FIM","N PALLETS","SACOS (UN)","RASGADOS","PARADAS"];
    let largura = 190/colunas.length;
    let altura = 8;

    colunas.forEach((c,i)=>{
        pdf.rect(10+i*largura,y,largura,altura);
        pdf.text(c,10+i*largura+1,y+5);
    });

    y+=altura;

    while(y < 285){
        for(let j=0;j<colunas.length;j++){
            pdf.rect(10+j*largura,y,largura,altura);
        }
        y+=altura;
    }

    const pdfBytes = pdf.output('arraybuffer');
    const mergedPdf = await PDFLib.PDFDocument.create();

    const pdfPrincipal = await PDFLib.PDFDocument.load(pdfBytes);
    const pagesPrincipal = await mergedPdf.copyPages(pdfPrincipal, pdfPrincipal.getPageIndices());
    pagesPrincipal.forEach(p => mergedPdf.addPage(p));

    if(arquivosRancho[ordem]){
        const file = arquivosRancho[ordem];
        const bytes = await file.arrayBuffer();

        const pdfRancho = await PDFLib.PDFDocument.load(bytes);
        const pagesRancho = await mergedPdf.copyPages(pdfRancho, pdfRancho.getPageIndices());
        pagesRancho.forEach(p => mergedPdf.addPage(p));
    }

    const finalPdf = await mergedPdf.save();

    const blob = new Blob([finalPdf], { type: 'application/pdf' });
    const link = document.createElement('a');

    link.href = URL.createObjectURL(blob);
    link.download = "ordem_com_rancho.pdf";
    link.click();
}
</script>

</head>
<body>
"""

# LOOP
for linha, datas in estrutura.items():

    bloco = f"<div class='linha'><h2>{linha}</h2>"

    for data, turnos in datas.items():

        bloco += f"<h3>📅 {data}</h3><div class='cards'>"

        for turno, itens in turnos.items():

            for item in itens:

                produto = item.get("Produto", "")
                ordem = item.get("Ordem", "")
                status = item.get("Status", "")

                qtde_total = item.get("Qtde Total", "0")
                qtde_pendente = item.get("Qtde Pendente", "0")

                total = to_float(qtde_total)
                pendente = to_float(qtde_pendente)

                if pendente == 0:
                    classe = "finalizado"
                elif pendente < total:
                    classe = "producao"
                else:
                    classe = "pendente"

                bloco += f"""
                <div class='card {classe}'>
                <b>{produto}</b><br>
                Ordem: {ordem}<br>
                Turno: {turno}<br>
                Qtde: {qtde_total}<br>
                Pendente: {qtde_pendente}<br>
                Status: {status}<br><br>

                <input type="file" accept="application/pdf"
                onchange="salvarRancho('{ordem}', this)">

                <button onclick="exportarCard(
                    '{produto}',
                    '{ordem}',
                    '{turno}',
                    '{qtde_total}',
                    '{qtde_pendente}',
                    '{status}',
                    '{data}',
                    '{linha}'
                )">📄 Gerar PDF</button>

                </div>
                """

        bloco += "</div>"

    bloco += "</div>"
    html += bloco

html += "</body></html>"

st.components.v1.html(html, height=900, scrolling=True)

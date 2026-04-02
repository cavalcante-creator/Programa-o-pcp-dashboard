# 🔥 SUBSTITUA SOMENTE A PARTE DO HTML POR ESSA

html = """
<html>
<head>

<!-- LIBS PDF -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<style>
body {
    font-family: 'Segoe UI', Arial;
    background: #f5f7fa;
    margin: 20px;
}

.linha {
    margin-bottom: 30px;
}

.linha h2 {
    background: #2c3e50;
    color: white;
    padding: 10px;
    border-radius: 8px;
    font-weight: 500;
}

.btn-export {
    margin: 10px 0;
    padding: 6px 12px;
    background: #2c3e50;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
}

.cards {
    display: flex;
    flex-wrap: wrap;
}

.card {
    width: 260px;
    padding: 12px;
    margin: 8px;
    border-radius: 12px;
    font-size: 13px;
    background: white;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
    border-left: 5px solid transparent;
}

.falta { border-left: 5px solid #e74c3c; }
.ok { border-left: 5px solid #2ecc71; }
.sobra { border-left: 5px solid #f1c40f; }
.atrasado { border-left: 5px solid #c0392b; }
</style>

<script>
async function exportarPDF(id) {
    const { jsPDF } = window.jspdf;

    let elemento = document.getElementById(id);

    const canvas = await html2canvas(elemento, { scale: 2 });

    const imgData = canvas.toDataURL("image/png");

    const pdf = new jsPDF('p', 'mm', 'a4');

    const largura = 190;
    const altura = (canvas.height * largura) / canvas.width;

    pdf.addImage(imgData, 'PNG', 10, 10, largura, altura);

    pdf.save("programacao_pcp.pdf");
}
</script>

</head>
<body>
"""

contador_id = 0

for linha, datas in estrutura.items():

    if linha_sel != "Todas" and linha != linha_sel:
        continue

    bloco_linha = f"<div class='linha' id='linha_{contador_id}'>"
    bloco_linha += f"<h2>{linha}</h2>"

    # 🔥 BOTÃO PDF
    bloco_linha += f"""
    <button class='btn-export' onclick="exportarPDF('linha_{contador_id}')">
    📄 Exportar PDF
    </button>
    """

    tem_conteudo_linha = False

    for data, turnos in datas.items():

        if semanas_sel and get_semana(data) not in semanas_sel:
            continue

        if not mostrar_todas and data != data_sel:
            continue

        tem_conteudo_data = False
        bloco_data = f"<h3>📅 {data}</h3>"

        for turno, itens in turnos.items():

            if turno_sel != "Todos" and turno != turno_sel:
                continue

            cards_html = ""
            tem_turno = False

            for item in itens:
                tem_turno = True

                status = item.get("Status", "").lower()

                if "falta" in status:
                    classe = "falta"
                elif "sobra" in status:
                    classe = "sobra"
                elif "atras" in status:
                    classe = "atrasado"
                else:
                    classe = "ok"

                cards_html += f"""
                <div class='card {classe}'>
                <b>{item.get("Produto")}</b><br>
                Ordem: {item.get("Ordem")}<br>
                Qtde: {item.get("Qtde Total")}<br>
                Status: {item.get("Status")}
                </div>
                """

            if tem_turno:
                tem_conteudo_data = True
                bloco_data += f"<b>Turno: {turno}</b><div class='cards'>{cards_html}</div>"

        if tem_conteudo_data:
            tem_conteudo_linha = True
            bloco_linha += bloco_data

    bloco_linha += "</div>"

    if tem_conteudo_linha:
        html += bloco_linha
        contador_id += 1

html += "</body></html>"

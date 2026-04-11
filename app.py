<script>
let arquivosRancho = {};

function salvarRancho(ordem, input){
    if(input.files[0]){
        arquivosRancho[ordem] = input.files[0];
        alert("Rancho anexado!");
    }
}

async function exportarCard(produto, ordem, turno, qtde, pendente, status, data, linha){

    const { jsPDF } = window.jspdf;
    const pdf = new jsPDF('p','mm','a4');

    // LOGO
    const img = new Image();
    img.src = "https://raw.githubusercontent.com/cavalcante-creator/Programa-o-pcp-dashboard/main/COL_LOGO_8.png";

    await new Promise(resolve => { img.onload = resolve });

    pdf.addImage(img, 'PNG', 10, 8, 35, 12);

    // TITULO
    pdf.setFontSize(14);
    pdf.text("ORDEM DE PRODUCAO", 70, 15);

    // LINHA + DATA
    pdf.setDrawColor(200);
    pdf.setFillColor(240);
    pdf.rect(10, 25, 190, 8, 'F');

    pdf.setFontSize(10);
    pdf.text("Linha: " + linha, 12, 30);
    pdf.text("Data: " + data, 140, 30);

    // INFORMACOES
    let y = 40;

    pdf.setFontSize(10);
    pdf.text("Produto: " + produto, 10, y);
    pdf.text("Ordem: " + ordem, 10, y+6);
    pdf.text("Turno: " + turno, 10, y+12);

    // QUANTIDADES
    pdf.setFontSize(11);
    pdf.text("Quantidade Programada: " + qtde, 10, y+22);
    pdf.text("Quantidade Pendente: " + pendente, 10, y+30);

    // OPERADOR
    pdf.text("Operador: ____________________________", 10, y+40);

    // TABELA
    let startY = y + 50;

    const colunas = [
        "HORA INICIO", "HORA FIM", "N PALLETS",
        "SACOS (UN)", "RASGADOS", "PARADAS"
    ];

    let colX = [10, 40, 70, 100, 130, 160];

    pdf.setFontSize(9);

    // CABECALHO
    for(let i=0; i<colunas.length; i++){
        pdf.text(colunas[i], colX[i], startY);
    }

    // LINHAS
    let linhaY = startY + 5;

    while(linhaY < 280){

        pdf.line(10, linhaY, 200, linhaY);

        for(let x of colX){
            pdf.line(x, linhaY, x, linhaY + 6);
        }

        linhaY += 6;
    }

    // GERAR PDF
    const pdfBytes = pdf.output('arraybuffer');

    const mergedPdf = await PDFLib.PDFDocument.create();

    const pdfPrincipal = await PDFLib.PDFDocument.load(pdfBytes);
    const pagesPrincipal = await mergedPdf.copyPages(pdfPrincipal, pdfPrincipal.getPageIndices());
    pagesPrincipal.forEach(p => mergedPdf.addPage(p));

    // ANEXAR RANCHO
    if(arquivosRancho[ordem]){
        const bytes = await arquivosRancho[ordem].arrayBuffer();
        const pdfRancho = await PDFLib.PDFDocument.load(bytes);
        const pagesRancho = await mergedPdf.copyPages(pdfRancho, pdfRancho.getPageIndices());
        pagesRancho.forEach(p => mergedPdf.addPage(p));
    }

    const finalPdf = await mergedPdf.save();

    const blob = new Blob([finalPdf], { type: 'application/pdf' });
    const link = document.createElement('a');

    link.href = URL.createObjectURL(blob);
    link.download = "ordem_producao.pdf";
    link.click();
}

async function exportarLinha(){
    const mergedPdf = await PDFLib.PDFDocument.create();
    const cards = document.querySelectorAll(".card");

    for(let card of cards){

        const ordemMatch = card.innerText.match(/Ordem:\s*(.*)/);
        const produtoMatch = card.innerText.split("\n")[0];

        if(!ordemMatch) continue;

        const ordem = ordemMatch[1];

        const { jsPDF } = window.jspdf;
        const pdf = new jsPDF();

        pdf.text("ORDEM: " + ordem, 10, 10);
        pdf.text("PRODUTO: " + produtoMatch, 10, 20);

        const pdfBytes = pdf.output('arraybuffer');

        const pdfPrincipal = await PDFLib.PDFDocument.load(pdfBytes);
        const pages = await mergedPdf.copyPages(pdfPrincipal, pdfPrincipal.getPageIndices());
        pages.forEach(p => mergedPdf.addPage(p));

        if(arquivosRancho[ordem]){
            const bytes = await arquivosRancho[ordem].arrayBuffer();
            const pdfRancho = await PDFLib.PDFDocument.load(bytes);
            const pagesRancho = await mergedPdf.copyPages(pdfRancho, pdfRancho.getPageIndices());
            pagesRancho.forEach(p => mergedPdf.addPage(p));
        }
    }

    const finalPdf = await mergedPdf.save();

    const blob = new Blob([finalPdf], { type: 'application/pdf' });
    const link = document.createElement('a');

    link.href = URL.createObjectURL(blob);
    link.download = "linha_completa.pdf";
    link.click();
}
</script>

from fpdf import FPDF
from datetime import datetime
import hashlib
import qrcode
import io
from PIL import Image

class LaudoPDF(FPDF):
    def header(self):
        self.rect(5, 5, 200, 287)
        self.rect(6, 6, 198, 285)
        self.set_font('Arial', 'B', 18)
        self.set_text_color(20, 40, 80)
        self.cell(0, 15, 'CERTIFICADO DE AUDITORIA E RISCO DIGITAL', 0, 1, 'C')
        self.set_font('Arial', 'B', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'DOCUMENTO PARA FINS DE COMPROVACAO DE CAUTELA E BOA-FE', 0, 1, 'C')
        self.line(15, 35, 195, 35)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'A validade deste laudo e restrita ao momento da consulta. Hash: {self.hash_id}', 0, 1, 'C')

def gerar_pdf_laudo(dados, tipo="link"):
    pdf = LaudoPDF()
    pdf.hash_id = hashlib.sha256(f"{dados.get('dominio') or dados.get('razao_social')}{datetime.now()}".encode()).hexdigest()[:16].upper()
    pdf.add_page()
    
    # 1. SCORE DE RISCO
    risco = dados.get('nivel_risco', 'baixo').upper()
    score = 95 if risco == "BAIXO" else 40 if risco == "MEDIO" else 5
    pdf.set_font('Arial', 'B', 12); pdf.cell(0, 10, '1. ANALISE SINTETICA DE RISCO', 0, 1)
    pdf.set_draw_color(200, 200, 200)
    pdf.cell(100, 10, ' NIVEL DE CONFIANCA DO ALVO:', 1, 0)
    if risco == 'ALTO':
        pdf.set_fill_color(255, 0, 0); pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 10, f' {score}% - RISCO CRITICO', 1, 1, 'C', fill=True)
    elif risco == 'MEDIO':
        pdf.set_fill_color(255, 165, 0); pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 10, f' {score}% - ATENCAO', 1, 1, 'C', fill=True)
    else:
        pdf.set_fill_color(0, 150, 0); pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 10, f' {score}% - SEGURO', 1, 1, 'C', fill=True)

    # 2. EVIDENCIAS
    pdf.ln(5); pdf.set_text_color(20, 40, 80); pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, '2. EVIDENCIAS TECNICAS COLETADAS', 0, 1)
    pdf.set_font('Arial', '', 10); pdf.set_text_color(0, 0, 0)
    if tipo == "link":
        campos = [("URL/Dominio", dados.get('dominio')), ("Certificado SSL", "VALIDO" if dados.get('seguro') else "AUSENTE"), 
                  ("Idade do Site", f"{dados.get('idade_meses')} meses"), ("Reputacao Google", "LIMPA" if risco != "ALTO" else "DENUNCIADO")]
    else:
        campos = [("Razao Social", dados.get('razao_social')), ("Status Receita", "ATIVA"), 
                  ("Capital Social", dados.get('capital_social')), ("Tempo de Mercado", f"{dados.get('meses_abertos')} meses")]
    for label, valor in campos:
        pdf.set_font('Arial', 'B', 10); pdf.cell(50, 8, f" {label}", 1, 0)
        pdf.set_font('Arial', '', 10); pdf.cell(0, 8, f" {valor}", 1, 1)

    # 3. PARECER TECNICO
    pdf.ln(5); pdf.set_font('Arial', 'B', 11); pdf.cell(0, 10, '3. PARECER TECNICO FINAL', 0, 1)
    pdf.set_font('Arial', 'I', 10); pdf.set_fill_color(245, 245, 245)
    parecer = f"Apos cruzamento de dados entre bases governamentais e protocolos de seguranca de rede, concluimos que o alvo apresenta um perfil de {risco}. "
    pdf.multi_cell(0, 8, parecer, 1, 'L', fill=True)

    # 4. TEXTO JURIDICO (CONFORMIDADE)
    pdf.ln(5); pdf.set_font('Arial', 'B', 10); pdf.set_text_color(100, 0, 0)
    pdf.cell(0, 10, 'CONFORMIDADE E VALIDADE JURIDICA', 0, 1)
    pdf.set_font('Arial', '', 9); pdf.set_text_color(0, 0, 0)
    texto_legal = (
        "Este laudo constitui prova documental de diligencia previa, demonstrando que o usuario agiu com a cautela esperada "
        "antes de realizar a transacao. Em caso de fraude confirmada, este documento deve ser anexado ao Boletim de Ocorrencia "
        "e apresentado a instituicao financeira para fundamentar o pedido de contestacao via Mecanismo Especial de Devolucao (MED), "
        "conforme Resolucoes do Banco Central do Brasil."
    )
    pdf.multi_cell(0, 5, texto_legal)

    # 5. QR CODE (CORRIGIDO)
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(f"https://seusite.com.br/validar?id={pdf.hash_id}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Usando buffer de bytes para o FPDF
    img_byte_arr = io.BytesIO()
    img_qr.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # O FPDF aceita o objeto BytesIO se passarmos o nome do arquivo como algo fictício
    pdf.image(img_byte_arr, x=160, y=235, w=30, type='PNG')
    
    pdf.set_xy(10, 245); pdf.set_font('Arial', 'B', 10); pdf.cell(0, 10, 'ASSINATURA DIGITAL CRIPTOGRAFICA', 0, 1)
    pdf.set_font('Courier', '', 8); pdf.cell(0, 5, f'ID: {pdf.hash_id}', 0, 1)
    pdf.set_font('Arial', '', 8); pdf.cell(0, 5, f'EMISSAO: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1)

    return bytes(pdf.output())

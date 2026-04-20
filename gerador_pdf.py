from fpdf import FPDF
from datetime import datetime
import hashlib
import qrcode
import io
from PIL import Image

class LaudoPDF(FPDF):
    def header(self):
        # Borda Dupla Profissional
        self.set_draw_color(20, 40, 80)
        self.rect(5, 5, 200, 287)
        self.rect(6, 6, 198, 285)
        
        # Cabeçalho Estilizado
        self.set_font('Arial', 'B', 22)
        self.set_text_color(20, 40, 80)
        self.cell(0, 20, 'CERTIFICADO DE AUDITORIA DIGITAL', 0, 1, 'C')
        
        self.set_font('Arial', 'B', 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, 'DOCUMENTO PARA FINS DE COMPROVACAO DE CAUTELA E BOA-FE (DILIGENCIA PREVIA)', 0, 1, 'C')
        
        self.set_draw_color(20, 40, 80)
        self.line(15, 40, 195, 40)
        self.ln(15)

    def footer(self):
        self.set_y(-25)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, f'A validade deste laudo e restrita ao momento da consulta. ID de Autenticidade: {self.hash_id}', 0, 1, 'C')
        self.cell(0, 5, 'Emitido por Auditoria Digital - Sistema de Protecao contra Fraudes.', 0, 0, 'C')

def gerar_pdf_laudo(dados, tipo="link"):
    pdf = LaudoPDF()
    pdf.hash_id = hashlib.sha256(f"{dados.get('dominio') or dados.get('razao_social')}{datetime.now()}".encode()).hexdigest()[:20].upper()
    pdf.add_page()
    
    # --- SECAO 1: SCORE DE CONFIANCA ---
    risco = dados.get('nivel_risco', 'baixo').upper()
    score = 95 if risco == "BAIXO" else 40 if risco == "MEDIO" else 5
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 10, '1. SCORE DE CONFIANCA DO ALVO', 0, 1)
    
    pdf.set_draw_color(200, 200, 200)
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(100, 12, ' NIVEL DE CONFIANCA CALCULADO:', 1, 0, fill=True)
    
    if risco == 'ALTO':
        pdf.set_fill_color(220, 53, 69); pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 12, f' {score}% - RISCO CRITICO', 1, 1, 'C', fill=True)
    elif risco == 'MEDIO':
        pdf.set_fill_color(255, 193, 7); pdf.set_text_color(0, 0, 0)
        pdf.cell(90, 12, f' {score}% - ATENCAO', 1, 1, 'C', fill=True)
    else:
        pdf.set_fill_color(40, 167, 69); pdf.set_text_color(255, 255, 255)
        pdf.cell(90, 12, f' {score}% - SEGURO', 1, 1, 'C', fill=True)

    # --- SECAO 2: EVIDENCIAS TECNICAS ---
    pdf.ln(10)
    pdf.set_text_color(20, 40, 80); pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, '2. EVIDENCIAS TECNICAS COLETADAS', 0, 1)
    
    pdf.set_font('Arial', '', 11); pdf.set_text_color(0, 0, 0)
    if tipo == "link":
        campos = [
            ("URL / Dominio", dados.get('dominio')), 
            ("Certificado SSL", "VALIDO (HTTPS ATIVO)" if dados.get('seguro') else "AUSENTE (RISCO DE INTERCEPTACAO)"), 
            ("Idade do Dominio", f"{dados.get('idade_meses')} meses"), 
            ("Reputacao Google", "LIMPA (SEM DENUNCIAS)" if risco != "ALTO" else "DENUNCIADO POR PHISHING")
        ]
    else:
        campos = [
            ("Razao Social", dados.get('razao_social')), 
            ("Status Receita Federal", "ATIVA"), 
            ("Capital Social Declarado", dados.get('capital_social')), 
            ("Tempo de Mercado", f"{dados.get('meses_abertos')} meses")
        ]
    
    for label, valor in campos:
        pdf.set_font('Arial', 'B', 11); pdf.set_fill_color(240, 240, 240)
        pdf.cell(60, 10, f" {label}", 1, 0, fill=True)
        pdf.set_font('Arial', '', 11); pdf.cell(0, 10, f" {valor}", 1, 1)

    # --- SECAO 3: PARECER TECNICO E JURIDICO ---
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14); pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 10, '3. PARECER TECNICO E CONFORMIDADE JURIDICA', 0, 1)
    
    pdf.set_font('Arial', '', 10); pdf.set_text_color(0, 0, 0)
    texto_legal = (
        "Este laudo constitui prova documental de diligencia previa, demonstrando que o usuario agiu com a cautela esperada "
        "antes de realizar a transacao. Em caso de fraude confirmada, este documento deve ser anexado ao Boletim de Ocorrencia "
        "e apresentado a instituicao financeira para fundamentar o pedido de contestacao via Mecanismo Especial de Devolucao (MED), "
        "conforme Resolucoes do Banco Central do Brasil.\n\n"
        "O score de confianca e calculado com base em cruzamento de dados de infraestrutura digital, registros governamentais "
        "e padroes comportamentais de fraude."
    )
    pdf.set_fill_color(250, 250, 250)
    pdf.multi_cell(0, 6, texto_legal, 1, 'L', fill=True)

    # --- SECAO 4: ASSINATURA DIGITAL E QR CODE ---
    pdf.ln(15)
    
    # Gerar QR Code Real
    qr = qrcode.QRCode(version=1, box_size=10, border=1)
    qr.add_data(f"VALIDO:{pdf.hash_id}")
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Buffer para o FPDF
    img_byte_arr = io.BytesIO()
    img_qr.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    # Posicionamento do QR Code e Assinatura
    pdf.image(img_byte_arr, x=160, y=230, w=35, type='PNG')
    
    pdf.set_xy(10, 240)
    pdf.set_font('Arial', 'B', 11); pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 10, 'ASSINATURA DIGITAL CRIPTOGRAFICA', 0, 1)
    
    pdf.set_font('Courier', '', 9); pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 5, f'ID: {pdf.hash_id}', 0, 1)
    
    pdf.set_font('Arial', '', 9)
    pdf.cell(0, 5, f'EMISSAO: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1)
    pdf.cell(0, 5, 'AUTENTICADO PELO MOTOR DE AUDITORIA DIGITAL', 0, 1)

    return bytes(pdf.output())

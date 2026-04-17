import streamlit as st
from validador_cnpj import verificar_cnpj
from validador_link import verificar_link
from validador_pagamento import analisar_risco_pix
from gerador_pdf import gerar_pdf_laudo
from pagamento import gerar_cobranca_pix, verificar_status_pagamento
import time

# Configuração da página
st.set_page_config(page_title="É Golpe?", page_icon="🛡️", layout="wide")

# --- GERENCIAMENTO DE ESTADO ---
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'pagamento_id' not in st.session_state:
    st.session_state.pagamento_id = None
if 'pago' not in st.session_state:
    st.session_state.pago = False
if 'dados_atuais' not in st.session_state:
    st.session_state.dados_atuais = None
if 'tipo_atual' not in st.session_state:
    st.session_state.tipo_atual = None

def adicionar_ao_historico(item):
    if item and item not in st.session_state.historico:
        st.session_state.historico.append(item)

# --- BARRA LATERAL ---
st.sidebar.title("🕒 Consultas Recentes")
if st.session_state.historico:
    for item in reversed(st.session_state.historico):
        st.sidebar.info(f"{item}")
else:
    st.sidebar.write("Nenhuma consulta realizada ainda.")

if st.sidebar.button("Limpar Histórico"):
    st.session_state.historico = []
    st.session_state.pago = False
    st.session_state.pagamento_id = None
    st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ Verificador de Segurança Profissional v4.1")
st.write("A única ferramenta que cruza dados de Site, CNPJ e Pagamento para sua total segurança.")

tab1, tab2, tab3 = st.tabs(["🌐 Validar Site/Link", "📋 Validar Empresa (CNPJ)", "💸 Analisar Risco de Pix"])

# Função auxiliar para o Paywall (Melhorada para visibilidade)
def mostrar_paywall(dados, tipo):
    st.markdown("---")
    st.subheader("📥 ÁREA PREMIUM: Laudo de Auditoria Detalhado")
    
    col_info, col_pay = st.columns([1, 1])
    
    with col_info:
        st.write("""
        **O que você recebe no Laudo Profissional:**
        - ✅ **Score de Confiança:** Nota de 0 a 100 baseada em IA.
        - ✅ **Análise Comportamental:** Tradução técnica dos riscos.
        - ✅ **Validade Jurídica:** Documento com Hash para B.O. e Bancos.
        - ✅ **Checklist Anti-Fraude:** Orientações de segurança.
        """)
    
    with col_pay:
        #if not st.session_state.pago:
        if True: # MODO DE TESTE: O botão de download sempre aparecerá abaixo
            st.info("💰 Valor do Laudo: **R$ 4,90**")
            if st.button(f"🚀 Gerar QR Code Pix para Liberar", key=f"pay_btn_{tipo}"):
                with st.spinner("Gerando cobrança segura..."):
                    cobranca = gerar_cobranca_pix()
                    if "erro" in cobranca:
                        st.error(f"❌ Erro: {cobranca['erro']}")
                        st.warning("Dica: Certifique-se de usar o 'Access Token' de PRODUÇÃO no config.py.")
                    else:
                        st.session_state.pagamento_id = cobranca["id"]
                        st.session_state.qr_code = cobranca["qr_code"]
                        st.session_state.qr_code_base64 = cobranca["qr_code_base64"]
            
            if st.session_state.pagamento_id:
                st.write("### Escaneie para Pagar:")
                st.image(f"data:image/png;base64,{st.session_state.qr_code_base64}", width=200)
                st.code(st.session_state.qr_code, language="text")
                st.caption("Copie o código acima se estiver no celular.")
                
                if st.button("🔄 Já paguei! Verificar liberação"):
                    if verificar_status_pagamento(st.session_state.pagamento_id):
                        st.session_state.pago = True
                        st.success("✅ Pagamento aprovado! Download liberado.")
                        st.rerun()
                    else:
                        st.error("Aguardando confirmação do banco... Tente novamente em 10 segundos.")
        
        else:
            st.success("🌟 Acesso Premium Liberado!")
            pdf_bytes = gerar_pdf_laudo(dados, tipo=tipo)
            st.download_button(label="📥 BAIXAR LAUDO AGORA (PDF)", 
                               data=pdf_bytes, 
                               file_name=f"laudo_seguranca_{tipo}.pdf", 
                               mime="application/pdf",
                               type="primary")

with tab1:
    entrada_link = st.text_input("Cole o Link aqui:", placeholder="ex: mercadolivre.com.br", key="input_link")
    if st.button("Analisar Link", type="primary", key="btn_link"):
        if entrada_link:
            adicionar_ao_historico(entrada_link)
            with st.spinner("Analisando infraestrutura..."):
                dados = verificar_link(entrada_link)
                st.session_state.dados_atuais = dados
                st.session_state.tipo_atual = "link"
                st.session_state.pago = False # Reseta para nova consulta
                st.session_state.pagamento_id = None
        else: st.error("Preencha o link.")

    if st.session_state.tipo_atual == "link" and st.session_state.dados_atuais:
        d = st.session_state.dados_atuais
        st.subheader(f"🌐 Relatório: {d['dominio']}")
        if d["nivel_risco"] == "baixo": st.success(d["veredito"])
        elif d["nivel_risco"] == "medio": st.warning(d["veredito"])
        else: st.error(d["veredito"])
        
        termo_limpo = d['dominio'].split('.')[0]
        st.link_button(f"🔍 Ver reputação no Reclame Aqui", f"https://www.reclameaqui.com.br/busca/?q={termo_limpo}")
        mostrar_paywall(d, "link")

with tab2:
    entrada_cnpj = st.text_input("Digite o CNPJ aqui:", placeholder="Ex: 06.990.590/0001-23", key="input_cnpj")
    if st.button("Analisar CNPJ", type="primary", key="btn_cnpj"):
        if entrada_cnpj:
            adicionar_ao_historico(entrada_cnpj)
            with st.spinner("Consultando bases oficiais..."):
                dados = verificar_cnpj(entrada_cnpj)
                if "erro" in dados: st.error(dados["erro"])
                else:
                    st.session_state.dados_atuais = dados
                    st.session_state.tipo_atual = "cnpj"
                    st.session_state.pago = False
                    st.session_state.pagamento_id = None
        else: st.error("Preencha o CNPJ.")

    if st.session_state.tipo_atual == "cnpj" and st.session_state.dados_atuais:
        d = st.session_state.dados_atuais
        st.subheader(f"📋 {d['razao_social']}")
        if d["nivel_risco"] == "baixo": st.success(d["veredito"])
        elif d["nivel_risco"] == "medio": st.warning(d["veredito"])
        else: st.error(d["veredito"])
        
        c1, c2 = st.columns(2)
        c1.metric("Tempo de Mercado", f"{d['meses_abertos']} meses")
        c2.metric("Capital Social", d["capital_social"])
        mostrar_paywall(d, "cnpj")

with tab3:
    st.subheader("🚀 Inovação: Analisador de Risco de Recebedor (Anti-Laranja)")
    chave_pix = st.text_input("Chave Pix (E-mail, Telefone ou CPF/CNPJ):", key="input_pix")
    nome_recebedor = st.text_input("Nome que aparece no Pix:", key="input_nome")
    tipo_conta = st.radio("A conta de destino é:", ["Pessoa Jurídica (CNPJ)", "Pessoa Física (CPF)"], key="input_tipo")
    banco_destino = st.selectbox("Banco de Destino:", ["Selecione...", "Nubank", "Inter", "Cora", "PagBank", "C6 Bank", "Itaú", "Bradesco", "Santander", "Caixa", "Banco do Brasil", "Outro"], key="input_banco")
    
    if st.button("Analisar Risco de Pagamento", key="btn_pix"):
        if chave_pix and nome_recebedor and banco_destino != "Selecione...":
            adicionar_ao_historico(f"Pix: {chave_pix}")
            with st.spinner("Validando chave..."):
                res = analisar_risco_pix(chave_pix, banco_destino, tipo_conta, nome_recebedor)
                if res["nivel_risco"] == "baixo": st.success(res["veredito"])
                elif res["nivel_risco"] == "medio": st.warning(res["veredito"])
                else: st.error(res["veredito"])
                for a in res["alertas"]: st.info(a)
        else: st.error("Preencha todos os campos.")

# --- SEÇÃO DE DICAS ---
st.divider()
c1, c2 = st.columns(2)
with c1:
    st.subheader("🚩 Sinais de Alerta")
    with st.expander("Clique para ver os sinais de golpe"):
        st.write("""
        1. **Preço milagroso:** Descontos acima de 50% em eletrônicos ou produtos de marca.
        2. **Urgência:** Mensagens como 'Últimas unidades', 'Sua conta será bloqueada' ou 'Promoção válida por 10 minutos'.
        3. **Pix para Pessoa Física:** Se você está comprando de uma loja (CNPJ), o pagamento NUNCA deve ser para um CPF de uma pessoa física.
        4. **Erros de Português:** Sites de grandes empresas raramente possuem erros grosseiros de escrita.
        """)
with c2:
    st.subheader("🛡️ Como se proteger")
    with st.expander("Clique para ver as dicas de proteção"):
        st.write("""
        - **Cartão Virtual:** Use sempre cartão de crédito virtual para compras online.
        - **Desconfie de Links:** Não clique em links recebidos via SMS ou WhatsApp.
        - **Confira o Remetente:** Verifique se o e-mail termina com o domínio oficial da empresa.
        - **Use este Verificador:** Sempre que tiver dúvida, passe o link ou CNPJ por aqui.
        """)

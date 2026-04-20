import streamlit as st
from validador_cnpj import verificar_cnpj
from validador_link import verificar_link
from validador_pagamento import analisar_risco_pix
from gerador_pdf import gerar_pdf_laudo
from pagamento import gerar_cobranca_pix, verificar_status_pagamento
import time

# --- CONFIGURAÇÃO DA PÁGINA (ESTILO SAAS) ---
st.set_page_config(page_title="É Golpe? | Auditoria Digital", page_icon="🛡️", layout="wide")

# CSS Customizado para Estilo Moderno (SiteChecker)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #0056b3; color: white; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    .card { background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; border-left: 5px solid #0056b3; }
    .metric-card { background-color: #ffffff; padding: 15px; border-radius: 10px; text-align: center; border: 1px solid #e0e0e0; }
    .status-safe { color: #28a745; font-weight: bold; }
    .status-warning { color: #ffc107; font-weight: bold; }
    .status-danger { color: #dc3545; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- GERENCIAMENTO DE ESTADO ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'pagamento_id' not in st.session_state: st.session_state.pagamento_id = None
if 'pago' not in st.session_state: st.session_state.pago = False
if 'dados_atuais' not in st.session_state: st.session_state.dados_atuais = None
if 'tipo_atual' not in st.session_state: st.session_state.tipo_atual = None

def adicionar_ao_historico(item):
    if item and item not in st.session_state.historico:
        st.session_state.historico.append(item)

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1162/1162456.png", width=80)
    st.title("Painel de Controle")
    st.markdown("---")
    st.subheader("🕒 Consultas Recentes")
    if st.session_state.historico:
        for item in reversed(st.session_state.historico):
            st.info(f"🔍 {item}")
    else: st.write("Nenhuma consulta.")
    if st.sidebar.button("Limpar Histórico"):
        st.session_state.historico = []; st.session_state.pago = False; st.rerun()

# --- ÁREA PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #002d5b;'>🛡️ Auditoria de Segurança Digital</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.2em; color: #666;'>A única plataforma que cruza dados de Site, CNPJ e Pagamento para sua total proteção.</p>", unsafe_allow_html=True)

# --- SISTEMA DE BUSCA UNIFICADO (ESTILO SITECHECKER) ---
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        entrada = st.text_input("", placeholder="Cole o Link (ex: site.com.br) ou CNPJ (ex: 00.000.000/0001-00) aqui...", label_visibility="collapsed")
    with col_btn:
        buscar = st.button("ANALISAR AGORA")
    st.markdown("</div>", unsafe_allow_html=True)

# --- LÓGICA DE PROCESSAMENTO ---
if buscar and entrada:
    adicionar_ao_historico(entrada)
    so_numeros = ''.join(filter(str.isdigit, entrada))
    
    with st.spinner("Realizando Auditoria Profissional..."):
        if len(so_numeros) == 14:
            st.session_state.dados_atuais = verificar_cnpj(entrada)
            st.session_state.tipo_atual = "cnpj"
        elif "." in entrada:
            st.session_state.dados_atuais = verificar_link(entrada)
            st.session_state.tipo_atual = "link"
        else:
            st.error("Formato inválido. Digite um CNPJ ou Link.")
        st.session_state.pago = False

# --- EXIBIÇÃO DE RESULTADOS (ESTILO DASHBOARD) ---
if st.session_state.dados_atuais:
    d = st.session_state.dados_atuais
    tipo = st.session_state.tipo_atual
    
    st.markdown(f"### 📊 Relatório de Auditoria: {d.get('dominio') or d.get('razao_social')}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.metric("Score de Confiança", f"{95 if d['nivel_risco'] == 'baixo' else 40 if d['nivel_risco'] == 'medio' else 5}/100")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        status_class = "status-safe" if d['nivel_risco'] == 'baixo' else "status-warning" if d['nivel_risco'] == 'medio' else "status-danger"
        st.markdown(f"Status: <span class='{status_class}'>{d['nivel_risco'].upper()}</span>", unsafe_allow_html=True)
        st.write(d['veredito'])
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        if tipo == "link":
            st.write(f"**SSL:** {'✅ Ativo' if d['seguro'] else '❌ Ausente'}")
            st.write(f"**Idade:** {d['idade_meses']} meses")
        else:
            st.write(f"**Capital:** {d['capital_social']}")
            st.write(f"**Tempo:** {d['meses_abertos']} meses")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ÁREA PREMIUM (PAYWALL) ---
    st.markdown("---")
    col_info, col_pay = st.columns([1, 1])
    with col_info:
        st.markdown("#### 📥 Obter Laudo de Auditoria Premium")
        st.write("O laudo contém o **Score de Coerência de Negócio**, análise de vínculo de fraude e validade jurídica.")
        st.info("💡 **Diferencial:** Este documento é aceito por bancos para contestação de Pix via MED.")
    
    with col_pay:
        # MODO DE TESTE PARA O USUÁRIO (LIBERADO)
        st.success("🌟 Acesso de Desenvolvedor: Download Liberado para Validação")
        pdf_bytes = gerar_pdf_laudo(d, tipo=tipo)
        st.download_button(label="📥 BAIXAR LAUDO AGORA (PDF)", 
                           data=pdf_bytes, 
                           file_name=f"laudo_auditoria_{tipo}.pdf", 
                           mime="application/pdf",
                           type="primary")
        
        st.markdown("---")
        st.write("Simulação de Pagamento (Para Clientes):")
        if st.button("Gerar Pix de R$ 4,90"):
            c = gerar_cobranca_pix()
            if "erro" not in c:
                st.image(f"data:image/png;base64,{c['qr_code_base64']}", width=150)
                st.code(c['qr_code'])

# --- ABA DE PIX (INOVAÇÃO) ---
st.markdown("---")
st.subheader("💸 Analisador de Risco de Pagamento (Anti-Laranja)")
with st.expander("Clique para validar dados de um recebedor Pix"):
    c1, c2 = st.columns(2)
    with c1:
        ch_pix = st.text_input("Chave Pix:")
        nm_rec = st.text_input("Nome do Recebedor:")
    with c2:
        tp_con = st.radio("Tipo de Conta:", ["Pessoa Jurídica (CNPJ)", "Pessoa Física (CPF)"])
        bc_des = st.selectbox("Banco:", ["Nubank", "Inter", "Cora", "PagBank", "Itaú", "Bradesco", "Santander", "Outro"])
    
    if st.button("Validar Recebedor"):
        res = analisar_risco_pix(ch_pix, bc_des, tp_con, nm_rec)
        if res["nivel_risco"] == "baixo": st.success(res["veredito"])
        else: st.error(res["veredito"])
        for a in res["alertas"]: st.info(a)

# --- FOOTER ---
st.markdown("---")
st.markdown("<p style='text-align: center; color: #999;'>© 2026 Auditoria Digital - Proteção Avançada contra Fraudes.</p>", unsafe_allow_html=True)

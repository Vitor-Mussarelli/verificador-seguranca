import streamlit as st
from validador_cnpj import verificar_cnpj
from validador_link import verificar_link
from validador_pagamento import analisar_risco_pix
from gerador_pdf import gerar_pdf_laudo
from pagamento import gerar_cobranca_pix, verificar_status_pagamento
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="É Golpe? | Auditoria Digital", page_icon="🛡️", layout="wide")

# CSS Corrigido: Removendo barras brancas e ajustando alinhamento
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stApp { background-color: #0e1117; }
    
    /* Remove as barras brancas dos containers */
    div[data-testid="stVerticalBlock"] > div > div > div[style*="background-color: white"] {
        background-color: #1e2129 !important;
        color: white !important;
        border: 1px solid #30363d !important;
    }
    
    .card { 
        background-color: #1e2129; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #30363d;
        margin-bottom: 20px; 
    }
    
    .metric-card { 
        background-color: #1e2129; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #30363d;
        min-height: 120px;
    }
    
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        background-color: #0056b3; 
        color: white; 
    }
    
    /* Ajuste para o campo de Banco no Pix */
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] {
        gap: 0.5rem;
    }
    
    h1, h2, h3, p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- GERENCIAMENTO DE ESTADO ---
if 'historico' not in st.session_state: st.session_state.historico = []
if 'dados_atuais' not in st.session_state: st.session_state.dados_atuais = None
if 'tipo_atual' not in st.session_state: st.session_state.tipo_atual = None
if 'score_cruzado' not in st.session_state: st.session_state.score_cruzado = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🛡️ Menu")
    st.subheader("🕒 Consultas Recentes")
    if st.session_state.historico:
        for item in reversed(st.session_state.historico):
            st.info(f"🔍 {item}")
    if st.button("Limpar Histórico"):
        st.session_state.historico = []; st.rerun()

# --- ÁREA PRINCIPAL ---
st.markdown("<h1 style='text-align: center;'>🛡️ Auditoria de Segurança Digital</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>A única plataforma que cruza dados de Site, CNPJ e Pagamento.</p>", unsafe_allow_html=True)

# --- BUSCA ---
with st.container():
    col_input, col_btn = st.columns([4, 1])
    with col_input:
        entrada = st.text_input("", placeholder="Cole o Link ou CNPJ aqui...", label_visibility="collapsed")
    with col_btn:
        buscar = st.button("ANALISAR")

if buscar and entrada:
    if entrada not in st.session_state.historico: st.session_state.historico.append(entrada)
    so_numeros = ''.join(filter(str.isdigit, entrada))
    
    with st.spinner("Cruzando dados..."):
        if len(so_numeros) == 14:
            st.session_state.dados_atuais = verificar_cnpj(entrada)
            st.session_state.tipo_atual = "cnpj"
        else:
            st.session_state.dados_atuais = verificar_link(entrada)
            st.session_state.tipo_atual = "link"
        
        # LÓGICA DE CRUZAMENTO INTELIGENTE
        # Se o usuário pesquisou um link, tentamos ver se ele também informou um CNPJ no passado recente
        # Ou se o próprio validador de link encontrou um CNPJ suspeito (futura expansão)
        st.session_state.score_cruzado = None # Reset

# --- RESULTADOS ---
if st.session_state.dados_atuais:
    d = st.session_state.dados_atuais
    tipo = st.session_state.tipo_atual
    
    st.markdown(f"### 📊 Resultado: {d.get('dominio') or d.get('razao_social')}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        score = 95 if d['nivel_risco'] == 'baixo' else 40 if d['nivel_risco'] == 'medio' else 5
        st.metric("Score de Confiança", f"{score}/100")
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        st.write(f"**Status:** {d['nivel_risco'].upper()}")
        st.write(d['veredito'])
        st.markdown("</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
        if tipo == "link":
            st.write(f"**SSL:** {'✅ Sim' if d['seguro'] else '❌ Não'}")
            st.write(f"**Idade:** {d['idade_meses']} meses")
        else:
            st.write(f"**Capital:** {d['capital_social']}")
            st.write(f"**Tempo:** {d['meses_abertos']} meses")
        st.markdown("</div>", unsafe_allow_html=True)

    # --- ÁREA DE PAGAMENTO / LAUDO ---
    st.markdown("---")
    col_info, col_pay = st.columns(2)
    with col_info:
        st.subheader("📥 Laudo de Auditoria Premium")
        st.write("Documento com validade jurídica para contestação bancária (MED).")
        pdf_bytes = gerar_pdf_laudo(d, tipo=tipo)
        st.download_button("📥 BAIXAR LAUDO (TESTE LIBERADO)", data=pdf_bytes, file_name="laudo.pdf", type="primary")
    with col_pay:
        st.write("Simular Pagamento Real:")
        if st.button("Gerar Pix de R$ 4,90"):
            c = gerar_cobranca_pix()
            if "erro" not in c:
                st.image(f"data:image/png;base64,{c['qr_code_base64']}", width=150)
                st.code(c['qr_code'])

# --- ANALISADOR DE PIX (CORRIGIDO ALINHAMENTO) ---
st.markdown("---")
st.subheader("💸 Analisador de Risco de Pagamento")
with st.expander("Validar Recebedor Pix", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        ch_pix = st.text_input("Chave Pix:")
        nm_rec = st.text_input("Nome do Recebedor:")
    with c2:
        tp_con = st.radio("Tipo de Conta:", ["Pessoa Jurídica (CNPJ)", "Pessoa Física (CPF)"])
        # O campo de banco agora está dentro de um container para evitar quebra de layout
        bc_des = st.selectbox("Banco de Destino:", ["Nubank", "Inter", "Cora", "PagBank", "Itaú", "Bradesco", "Santander", "Outro"])
    
    if st.button("Validar Pix"):
        res = analisar_risco_pix(ch_pix, bc_des, tp_con, nm_rec)
        if res["nivel_risco"] == "baixo": st.success(res["veredito"])
        else: st.error(res["veredito"])
        for a in res["alertas"]: st.info(a)

# --- RESTAURAÇÃO DAS DICAS (REMOVIDAS ANTERIORMENTE) ---
st.markdown("---")
col_d1, col_d2 = st.columns(2)
with col_d1:
    st.subheader("🚩 Sinais de Alerta")
    with st.expander("Ver Sinais de Golpe", expanded=True):
        st.write("""
        1. **Preço milagroso:** Descontos irreais em produtos caros.
        2. **Urgência:** Cronômetros e mensagens de 'últimas unidades'.
        3. **Pix para CPF:** Empresas reais usam Pix CNPJ.
        4. **Erros de Português:** Sites falsos costumam ter erros de escrita.
        """)
with col_d2:
    st.subheader("🛡️ Como se proteger")
    with st.expander("Ver Dicas de Segurança", expanded=True):
        st.write("""
        - **Cartão Virtual:** Use sempre para compras online.
        - **Confira o Link:** Verifique se o domínio é o oficial (ex: .com.br).
        - **Não clique em SMS:** Bancos não enviam links de urgência por SMS.
        - **Gere o Laudo:** Em caso de dúvida, use nosso laudo para se proteger.
        """)

st.markdown("<p style='text-align: center; color: #666; margin-top: 50px;'>© 2026 Auditoria Digital Profissional</p>", unsafe_allow_html=True)

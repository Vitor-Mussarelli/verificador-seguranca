import requests
import whois
from urllib.parse import urlparse
from datetime import datetime
from difflib import SequenceMatcher
import streamlit as st

# Tenta ler do st.secrets ou do config.py
try:
    GOOGLE_SAFE_BROWSING_API_KEY = st.secrets["GOOGLE_SAFE_BROWSING_API_KEY"]
except:
    try:
        import config
        GOOGLE_SAFE_BROWSING_API_KEY = getattr(config, 'GOOGLE_SAFE_BROWSING_API_KEY', "")
    except:
        GOOGLE_SAFE_BROWSING_API_KEY = ""

# --- CAMADA: Sites Conhecidos ---
SITES_CONFIAVEIS = {
    'google.com': 'Site oficial de buscas do Google.',
    'mercadolivre.com.br': 'Plataforma oficial do Mercado Livre.',
    'amazon.com.br': 'Site oficial da Amazon Brasil.',
    'facebook.com': 'Rede social oficial do Facebook.',
    'instagram.com': 'Rede social oficial do Instagram.',
    'youtube.com': 'Plataforma oficial do YouTube.',
    'apple.com': 'Site oficial da Apple.',
    'microsoft.com': 'Site oficial da Microsoft.',
    'gov.br': 'Portal oficial do Governo Federal.'
}

def verificar_similaridade(dominio):
    for confiavel in SITES_CONFIAVEIS.keys():
        ratio = SequenceMatcher(None, dominio, confiavel).ratio()
        if 0.8 < ratio < 1.0:
            return True, confiavel
    return False, None

@st.cache_data(ttl=3600)
def verificar_link(url_input):
    if not url_input.startswith(('http://', 'https://')):
        url_input = 'https://' + url_input
    
    try:
        parsed_url = urlparse(url_input)
        dominio = parsed_url.netloc if parsed_url.netloc else parsed_url.path
        if dominio.startswith('www.'): dominio = dominio[4:]
    except:
        return {"erro": "URL inválida"}

    # 1. Google Safe Browsing
    denunciado_google = False
    if GOOGLE_SAFE_BROWSING_API_KEY:
        try:
            api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_API_KEY}"
            payload = {
                "client": {"clientId": "egolpe-app", "clientVersion": "1.0.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url_input}]
                }
            }
            response = requests.post(api_url, json=payload, timeout=5)
            if response.status_code == 200 and response.json():
                denunciado_google = True
        except:
            pass

    # 2. SSL e Similaridade
    tem_ssl = url_input.startswith('https://')
    e_similar, site_original = verificar_similaridade(dominio)
    
    # 3. Idade do Domínio (WHOIS)
    idade_meses = 0
    data_formatada = "Não identificada"
    hoje = datetime.now()
    
    try:
        if dominio.endswith('.br'):
            res = requests.get(f"https://rdap.registro.br/domain/{dominio}", timeout=5)
            if res.status_code == 200:
                data_str = res.json()['events'][0]['eventDate']
                data_criacao = datetime.strptime(data_str[:10], '%Y-%m-%d')
                idade_meses = (hoje - data_criacao).days // 30
                data_formatada = data_criacao.strftime('%d/%m/%Y')
        else:
            w = whois.whois(dominio)
            data_criacao = w.creation_date
            if isinstance(data_criacao, list): data_criacao = data_criacao[0]
            if data_criacao:
                idade_meses = (hoje - data_criacao).days // 30
                data_formatada = data_criacao.strftime('%d/%m/%Y')
    except:
        pass

    # Lógica de Veredito
    dossie = {"dominio": dominio, "seguro": tem_ssl, "data_criacao": data_formatada, "idade_meses": idade_meses, "veredito": "", "nivel_risco": "baixo"}

    if denunciado_google:
        dossie["veredito"] = "🔴 SINAL VERMELHO: Denunciado pelo Google como PHISHING!"
        dossie["nivel_risco"] = "alto"
    elif e_similar:
        dossie["veredito"] = f"🔴 SINAL VERMELHO: Site muito parecido com o {site_original}."
        dossie["nivel_risco"] = "alto"
    elif dominio.endswith('.shop') and idade_meses < 6:
        dossie["veredito"] = "🔴 SINAL VERMELHO: Domínio .shop muito novo. Tática comum de golpistas."
        dossie["nivel_risco"] = "alto"
    elif not tem_ssl:
        dossie["veredito"] = "🔴 SINAL VERMELHO: Conexão não segura (sem HTTPS)."
        dossie["nivel_risco"] = "alto"
    elif idade_meses < 6:
        dossie["veredito"] = "🟡 SINAL AMARELO: Site muito novo. Cuidado extra."
        dossie["nivel_risco"] = "medio"
    elif dominio in SITES_CONFIAVEIS:
        dossie["veredito"] = f"🟢 SINAL VERDE: Este é um site oficial e verificado ({dominio}). Totalmente seguro."
        dossie["nivel_risco"] = "baixo"
        dossie["idade_meses"] = 999
    else:
        dossie["veredito"] = "🟢 SINAL VERDE: Domínio antigo e seguro."
        dossie["nivel_risco"] = "baixo"
    
    return dossie

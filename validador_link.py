import requests
import whois
from urllib.parse import urlparse
from datetime import datetime
from difflib import SequenceMatcher
import streamlit as st

# Tenta importar a chave da API, se não existir usa vazio
try:
    from config import GOOGLE_SAFE_BROWSING_API_KEY
except ImportError:
    GOOGLE_SAFE_BROWSING_API_KEY = ""

# --- NOVA CAMADA: Inteligência de Sites Conhecidos (Whitelisting) ---
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
    """Verifica se o domínio é muito parecido com um site confiável (Typosquatting)"""
    for confiavel in SITES_CONFIAVEIS.keys():
        ratio = SequenceMatcher(None, dominio, confiavel).ratio()
        if 0.8 < ratio < 1.0: # Similar mas não idêntico
            return True, confiavel
    return False, None

@st.cache_data(ttl=3600) # Cache de 1 hora
def verificar_link(url_input):
    # 1. Limpeza do Link
    if not url_input.startswith(('http://', 'https://')):
        url_input = 'http://' + url_input

    try:
        dominio = urlparse(url_input).netloc
        if dominio.startswith('www.'):
            dominio = dominio[4:]
    except:
        return {"erro": "Formato de link inválido."}

    # Se estiver na lista branca, já montamos o dicionário de sucesso imediato
    if dominio in SITES_CONFIAVEIS:
        return {
            "dominio": dominio,
            "seguro": True,
            "data_criacao": "Domínio verificado",
            "idade_meses": 999,
            "veredito": f"🟢 SINAL VERDE: Este é um site oficial e verificado ({dominio}). Totalmente seguro.",
            "nivel_risco": "baixo"
        }

    # --- Verificações de Risco ---
    tlds_perigosos = ['.shop', '.online', '.vip', '.site', '.top', '.click', '.app', '.store']
    tld_suspeito = any(dominio.endswith(tld) for tld in tlds_perigosos)

    # Verificação de Typosquatting
    e_similar, site_original = verificar_similaridade(dominio)

    # --- NOVA CAMADA: Google Safe Browsing (Phishing/Malware) ---
    denunciado_google = False
    if GOOGLE_SAFE_BROWSING_API_KEY:
        try:
            url_google = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={GOOGLE_SAFE_BROWSING_API_KEY}"
            payload = {
                "client": {"clientId": "egolpe-app", "clientVersion": "1.0.0"},
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": url_input}]
                }
            }
            res_google = requests.post(url_google, json=payload, timeout=5)
            if res_google.status_code == 200 and res_google.json():
                denunciado_google = True
        except:
            pass

    tem_ssl = False
    try:
        requests.get(f"https://{dominio}", timeout=3)
        tem_ssl = True
    except:
        tem_ssl = False

    data_criacao = None
    data_formatada = "Não identificada"
    idade_meses = 0
    hoje = datetime.now()

    try:
        if dominio.endswith('.br'):
            url_api = f"https://rdap.registro.br/domain/{dominio}"
            response = requests.get(url_api, timeout=5)
            if response.status_code != 404:
                dados = response.json()
                for evento in dados.get('events', []):
                    if evento.get('eventAction') == 'registration':
                        data_str = evento.get('eventDate').split('T')[0]
                        data_criacao = datetime.strptime(data_str, '%Y-%m-%d')
                        break
        else:
            dados_dominio = whois.whois(dominio)
            data_whois = dados_dominio.creation_date
            if isinstance(data_whois, list):
                data_criacao = data_whois[0]
            else:
                data_criacao = data_whois
            
            if not isinstance(data_criacao, datetime):
                data_criacao = None

        if data_criacao:
            idade_dias = (hoje - data_criacao).days
            idade_meses = idade_dias // 30
            data_formatada = data_criacao.strftime('%d/%m/%Y')

    except Exception:
        data_criacao = None 

    # --- Montando o Dicionário de Retorno ---
    dossie = {
        "dominio": dominio,
        "seguro": tem_ssl,
        "data_criacao": data_formatada,
        "idade_meses": idade_meses,
        "veredito": "",
        "nivel_risco": "baixo"
    }

    # Lógica de Veredito
    if denunciado_google:
        dossie["veredito"] = "🔴 SINAL VERMELHO: Este site foi denunciado pelo Google como PHISHING ou MALWARE!"
        dossie["nivel_risco"] = "alto"
    elif e_similar:
        dossie["veredito"] = f"🔴 SINAL VERMELHO: Este site é MUITO parecido com o {site_original}. Pode ser um golpe de clonagem!"
        dossie["nivel_risco"] = "alto"
    elif not tem_ssl:
        dossie["veredito"] = "🔴 SINAL VERMELHO: O site não possui conexão segura (HTTPS)."
        dossie["nivel_risco"] = "alto"
    elif tld_suspeito and idade_meses < 6:
        dossie["veredito"] = "🔴 SINAL VERMELHO: Extensão suspeita (.shop, .site, etc) e site muito novo."
        dossie["nivel_risco"] = "alto"
    elif data_criacao:
        if (hoje - data_criacao).days < 30:
            dossie["veredito"] = f"🔴 SINAL VERMELHO: Site criado há apenas {(hoje - data_criacao).days} dias."
            dossie["nivel_risco"] = "alto"
        elif idade_meses < 6:
            dossie["veredito"] = "🟡 SINAL AMARELO: Site muito novo. Cuidado extra."
            dossie["nivel_risco"] = "medio"
        else:
            dossie["veredito"] = "🟢 SINAL VERDE: Domínio antigo e seguro."
            dossie["nivel_risco"] = "baixo"
    else:
         dossie["veredito"] = "🟡 SINAL AMARELO: Não foi possível validar a idade. Verifique manualmente."
         dossie["nivel_risco"] = "medio"

    return dossie

if __name__ == "__main__":
    # Teste manual (sem cache)
    print(verificar_link.__wrapped__("google.com"))

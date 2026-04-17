import requests
from datetime import datetime
import streamlit as st

@st.cache_data(ttl=3600) # Cache de 1 hora para evitar requisições repetidas
def verificar_cnpj(cnpj_input):
    cnpj_limpo = ''.join(filter(str.isdigit, cnpj_input))
    
    if len(cnpj_limpo) != 14:
        return {"erro": "O CNPJ deve conter 14 números."}

    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_limpo}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return {"erro": "🚨 SINAL VERMELHO: CNPJ não encontrado na Receita Federal."}
        
        dados = response.json()
        
        # Coleta de dados
        razao_social = dados.get('razao_social')        
        situacao = dados.get('descricao_situacao_cadastral')
        data_abertura_str = dados.get('data_inicio_atividade')        
        capital_social = dados.get('capital_social', 0)
        cnae_principal = dados.get('cnae_fiscal_descricao')        
        
        email_bruto = dados.get('email')
        email_registro = email_bruto.lower() if email_bruto else "Não informado"
        
        # Cálculo de idade
        data_abertura = datetime.strptime(data_abertura_str, '%Y-%m-%d')
        hoje = datetime.now()
        meses_abertos = (hoje.year - data_abertura.year) * 12 + hoje.month - data_abertura.month
        data_formatada = data_abertura.strftime('%d/%m/%Y')

        # Análise de E-mail
        provedores_publicos = ['gmail.com', 'hotmail.com', 'outlook.com', 'yahoo.com', 'uol.com.br', 'bol.com.br']
        email_suspeito = any(prov in email_registro for prov in provedores_publicos)

        # Montando o Dicionário para o Site
        dossie = {
            "razao_social": razao_social,
            "data_abertura": data_formatada,
            "atividade": cnae_principal,
            "capital_social": f"R$ {capital_social:,.2f}",
            "email": email_registro,
            "meses_abertos": meses_abertos,
            "veredito": "",
            "nivel_risco": "baixo" # baixo, medio, alto
        }

        # Lógica de Veredito e Nível de Risco
        if situacao != "ATIVA":
            dossie["veredito"] = "🔴 SINAL VERMELHO: Empresa INATIVA ou CANCELADA."
            dossie["nivel_risco"] = "alto"
        elif meses_abertos < 12 and capital_social < 5000:
            dossie["veredito"] = "🔴 SINAL VERMELHO: Empresa muito nova com capital social baixíssimo. Risco de 'fachada'."
            dossie["nivel_risco"] = "alto"
        elif meses_abertos > 24 and email_suspeito:
            dossie["veredito"] = f"🟡 SINAL AMARELO: Empresa estabelecida mas usa e-mail amador ({email_registro})."
            dossie["nivel_risco"] = "medio"
        elif meses_abertos < 6:
            dossie["veredito"] = f"🟡 SINAL AMARELO: Empresa criada há pouco tempo ({meses_abertos} meses)."
            dossie["nivel_risco"] = "medio"
        else:
            dossie["veredito"] = "🟢 SINAL VERDE: Dados consistentes com uma operação real."
            dossie["nivel_risco"] = "baixo"

        return dossie

    except Exception as e:
        return {"erro": f"Erro na consulta: {e}"}

if __name__ == "__main__":
    # Teste rápido (sem streamlit cache quando rodado direto)
    print(verificar_cnpj.__wrapped__("06990590000123"))
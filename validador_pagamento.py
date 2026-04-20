import requests
try:
    import config
    ASAAS_API_KEY = getattr(config, 'ASAAS_API_KEY', "")
except ImportError:
    ASAAS_API_KEY = ""

def consultar_pix_real(chave):
    """
    Consulta real da chave Pix via API do Asaas.
    Nota: Exige ASAAS_API_KEY válida.
    """
    if not ASAAS_API_KEY:
        return {"erro": "API de consulta Pix não configurada."}
    
    url = "https://www.asaas.com/api/v3/pix/addressKeys/validate"
    headers = {
        "access_token": ASAAS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {"addressKey": chave}
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json() # Retorna dados reais do Banco Central
        return {"erro": f"Erro na consulta: {response.status_code}"}
    except Exception as e:
        return {"erro": str(e)}

def analisar_risco_pix(chave, banco_informado, tipo_conta, nome_informado):
    score_risco = 0
    alertas = []
    dados_reais = None

    # Se tivermos API, fazemos a consulta real
    if ASAAS_API_KEY:
        dados_reais = consultar_pix_real(chave)
        if "erro" not in dados_reais:
            nome_real = dados_reais.get("name", "").upper()
            banco_real = dados_reais.get("ispbName", "").upper()
            
            # Validação de Nome (Inovação)
            if nome_informado.upper() not in nome_real:
                score_risco += 60
                alertas.append(f"🔴 CRÍTICO: O nome informado ({nome_informado}) NÃO coincide com o titular da conta ({nome_real}).")
            
            # Validação de Banco
            if banco_informado.upper() not in banco_real:
                score_risco += 30
                alertas.append(f"⚠️ DIVERGÊNCIA: O banco informado é {banco_informado}, mas a chave está registrada no {banco_real}.")
        else:
            alertas.append(f"ℹ️ Consulta em tempo real indisponível: {dados_reais['erro']}")

    # Validações Heurísticas (Sempre ativas)
    if tipo_conta == "Pessoa Física (CPF)":
        score_risco += 40
        alertas.append("⚠️ ALERTA: Pagamento para CPF em transação comercial é um forte indício de golpe.")

    # Veredito
    if score_risco >= 50:
        veredito = "🔴 RISCO ALTO: Dados de pagamento altamente suspeitos ou divergentes."
        nivel = "alto"
    elif score_risco >= 20:
        veredito = "🟡 RISCO MÉDIO: Existem inconsistências que exigem atenção."
        nivel = "medio"
    else:
        veredito = "🟢 RISCO BAIXO: Dados de pagamento consistentes."
        nivel = "baixo"
        
    return {
        "veredito": veredito,
        "nivel_risco": nivel,
        "alertas": alertas,
        "dados_reais": dados_reais
    }

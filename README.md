# 🛡️ Verificador de Segurança Profissional - É Golpe?

Uma ferramenta avançada para proteção contra fraudes digitais, integrando análise de sites, consultas de CNPJ e verificação de risco de pagamentos Pix.

## 🚀 Funcionalidades
- **🌐 Validação de Links:** Identificação de typosquatting (sites clones), idade do domínio e reputação via Google Safe Browsing.
- **📋 Auditoria de CNPJ:** Consulta em tempo real à base da Receita Federal para verificar tempo de mercado e capital social.
- **💸 Analisador de Pix:** Verificação de inconsistências em chaves Pix e bancos digitais (Anti-Laranja).
- **📥 Laudos em PDF:** Geração de certificados de auditoria com validade jurídica para contestação bancária.

## 🛠️ Tecnologias
- Python 3.11
- Streamlit (Interface Web)
- FPDF2 (Geração de Laudos)
- APIs: Google Safe Browsing, BrasilAPI, Mercado Pago (Pagamentos).

## 📦 Como rodar localmente
1. Clone o repositório
2. Instale as dependências: `pip install -r requirements.txt`
3. Configure suas chaves no arquivo `config.py`
4. Execute: `streamlit run app.py`

## 💰 Monetização
Este projeto foi estruturado para o modelo Freemium, onde a consulta é gratuita e o laudo detalhado em PDF é vendido via integração com Mercado Pago.

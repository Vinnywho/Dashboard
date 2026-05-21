import streamlit as st
import pandas as pd
from openai import OpenAI

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def obter_insight_ia(nome_camp, metricas):
    try:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=st.secrets["GROQ_API_KEY"]
        )
        
        if 'prompt' in metricas:
            prompt = metricas['prompt']
        else:
            prompt = f"""
            Analise a campanha '{nome_camp}':
            - Clientes Impactados: {metricas.get('impactados', 0)}
            - Taxa de Conversão: {metricas.get('conversao', 0):.2f}%
            - Receita Gerada Diretamente: {formatar_moeda(metricas.get('receita_direta', 0))}
            Gere uma análise executiva curta e estratégica.
            """
            
        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Erro técnico: {str(e)}"

def processar_campanha(selecionada, campanhas_total, conversoes_total, pedidos_loja, mapa_lojas):
    dados_focados = campanhas_total[campanhas_total['name'] == selecionada]
    id_loja = dados_focados['storeid'].iloc[0] if 'storeid' in dados_focados.columns else None
    nome_loja = mapa_lojas.get(id_loja, f"Loja {id_loja}")
    clientes_imp = set(dados_focados['customerid'].dropna().unique())

    conv_vinculadas = conversoes_total[conversoes_total['customerid'].isin(clientes_imp)]
    if id_loja is not None and 'storeid' in conv_vinculadas.columns:
        conv_vinculadas = conv_vinculadas[conv_vinculadas['storeid'] == id_loja]

    col_order = next((c for c in ['order_id', 'orderid', 'ORDERID', 'id_pedido'] if c in conv_vinculadas.columns), None)
    col_store_pedidos = next((c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)

    if col_order:
        pedidos_conv = pedidos_loja[pedidos_loja['id'].isin(conv_vinculadas[col_order])]
    else:
        pedidos_conv = pd.DataFrame()

    if id_loja is not None and col_store_pedidos:
        pedidos_conv = pedidos_conv[pedidos_conv[col_store_pedidos] == id_loja]

    return clientes_imp, pedidos_conv, id_loja, nome_loja, col_store_pedidos
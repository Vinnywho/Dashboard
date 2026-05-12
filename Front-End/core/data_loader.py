import pandas as pd
import streamlit as st
import os

@st.cache_data
def carregar_dados():
    diretorio_core = os.path.dirname(os.path.abspath(__file__))
    raiz_projeto = os.path.dirname(os.path.dirname(diretorio_core))
    
    def get_path(nome_arquivo):
        caminhos = [
            os.path.join(raiz_projeto, "data", nome_arquivo),
            os.path.join(os.path.dirname(diretorio_core), "data", nome_arquivo),
            os.path.join(os.getcwd(), "data", nome_arquivo),
            os.path.join(os.getcwd(), "Front-End", "data", nome_arquivo)
        ]
        for c in caminhos:
            if os.path.exists(c):
                return c
        return os.path.join(raiz_projeto, "data", nome_arquivo)

    df_campanhas = pd.read_csv(get_path('CAMPAIGN.CSV'))
    df_conversoes = pd.read_csv(get_path('CAMPAIGNxORDER.CSV'))
    df_pedidos_loja = pd.read_csv(get_path('STOREORDER.csv'))
    df_stores = pd.read_csv(get_path('STORE.CSV'))
    df_clientes = pd.read_csv(get_path('CUSTOMER.CSV'))
    df_enderecos = pd.read_csv(get_path('CUSTOMERADDRESS.CSV'))

    df_campanhas['sendat'] = pd.to_datetime(df_campanhas['sendat'], errors='coerce')
    df_conversoes['sent_at'] = pd.to_datetime(df_conversoes['sent_at'], errors='coerce')
    df_pedidos_loja['createdat'] = pd.to_datetime(df_pedidos_loja['createdat'], errors='coerce')
    df_clientes['dateofbirth'] = pd.to_datetime(df_clientes['dateofbirth'], errors='coerce')

    mapa_lojas = dict(zip(df_stores['id'], df_stores['name']))

    return df_campanhas, df_conversoes, df_pedidos_loja, mapa_lojas, df_clientes, df_enderecos
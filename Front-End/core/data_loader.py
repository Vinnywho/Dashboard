import streamlit as st
import pandas as pd

@st.cache_data
def carregar_dados():
    df_campanhas = pd.read_csv('../data/CAMPAIGN.CSV')
    df_conversoes = pd.read_csv('../data/CAMPAIGNxORDER.CSV')
    df_pedidos_loja = pd.read_csv('../data/STOREORDER.csv')
    df_stores = pd.read_csv('../data/STORE.CSV')
    df_clientes = pd.read_csv('../data/CUSTOMER.CSV')
    df_enderecos = pd.read_csv('../data/CUSTOMERADDRESS.CSV')

    mapa_lojas = dict(zip(df_stores['id'], df_stores['name']))

    for df, col in [(df_campanhas, 'sendat'), (df_pedidos_loja, 'createdat'), (df_clientes, 'createdat')]:
        df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
    
    df_pedidos_loja['scheduledat'] = pd.to_datetime(df_pedidos_loja['scheduledat'], format='mixed')
    df_clientes['dateofbirth'] = pd.to_datetime(df_clientes['dateofbirth'], errors='coerce')

    return df_campanhas, df_conversoes, df_pedidos_loja, mapa_lojas, df_clientes, df_enderecos
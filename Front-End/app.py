import streamlit as st
import numpy as np
import pandas as pd
import os
import altair as alt

st.set_page_config(page_title="Análise de Performance", layout="wide")

# Injeção de CSS para estilizar os cards de métricas
st.markdown("""
    <style>
    .stApp { 
        background-color: ##FFE8E8; 
    }
    [data-testid="stHeading"] h1{
        color: #913322;
        font-weight: 900;
        text-transform: uppercase;
        font-family: 'Montserrat', sans-serif;
        text-align: center;
    }
    [data-testid="stMetric"] {
        display: flex;
        background-color: #B04735;
        color: #fff;
        padding: 15px;
        border-radius: 2rem;
        height: 125px;
        border: 1px solid #e0e0e06c;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        justify-content: center;
        align-items: center;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s, box-shadow 0.2s, background-color 0.2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
        background-color: #A34231;
    }
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: bold;
        color: #fff;
    }
    [data-testid="stMetricLabel"] {
        font-size: 16px;
        color: #fff;
        font-weight: bold;
    }
    [data-testid="stMetricDelta"] {
        font-size: 14px;
        color: #00ff6eff;
        font-weight: bold;
    }
    [data-testid="stMetricDeltaNegative"] {
        color: #ff4d4d;
    }      
    [data-testid="stMetricDeltaPositive"] {
        color: #00ff6eff;
    }
    [data-baseweb="select"] > div {
        border-radius: 2rem;
        border: 1px solid #00000062;
        justify-content: center;
        align-items: center;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        color: #565656FF;
        margin-bottom: 20px;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #913322 !important; /* Cor do texto acima do select */
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
#color = "#565656FF"

#-----------------------------------------------------------------------------------------------------------------------
st.title("Análise de Performance das Campanhas")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    df_campanhas = pd.read_csv('../data/CAMPAIGN.CSV')
    df_conversoes = pd.read_csv('../data/CAMPAIGNxORDER.CSV')
    df_pedidos_loja = pd.read_csv('../data/STOREORDER.csv')
    return df_campanhas, df_conversoes, df_pedidos_loja

#-----------------------------------------------------------------------------------------------------------------------

# Carregar os dados e pré-processar as datas
campanhas_total, conversoes_total, pedidos_loja = carregar_dados()

# Converter as colunas de data para datetime, tratando erros e garantindo que estejam no mesmo fuso horário
campanhas_total['sendat'] = pd.to_datetime(
    campanhas_total['sendat'], errors='coerce', utc=True)
pedidos_loja['createdat'] = pd.to_datetime(
    pedidos_loja['createdat'], errors='coerce', utc=True)

# Seleção da Campanha
lista_campanhas = sorted(campanhas_total['name'].unique())
campanha_selecionada = st.selectbox("Selecione a Campanha", lista_campanhas)

# Filtrar dados com base na campanha selecionada
dados_campanha_focada = campanhas_total[campanhas_total['name'] == campanha_selecionada]

#-----------------------------------------------------------------------------------------------------------------------

# Identificar clientes impactados por esta campanha específica
clientes_impactados = set(dados_campanha_focada['customerid'].dropna().unique())

# Buscar a coluna de ligação na tabela de conversões ou usar os clientes impactados como filtro
# Isso resolve o problema de colunas inexistentes ou IDs que não batem com nomes
coluna_id_referencia = next((c for c in ['campaignid', 'ID', 'id',
                  'CAMPAIGNID'] if c in conversoes_total.columns), None)

if coluna_id_referencia:
    # Se encontramos a coluna de ID, buscamos o ID real correspondente ao nome selecionado
    coluna_id_campanha = next(
        (c for c in ['ID', 'id', 'campaignid'] if c in campanhas_total.columns), None)
    id_campanha_real = dados_campanha_focada[coluna_id_campanha].iloc[0] if coluna_id_campanha else None

    if id_campanha_real is not None:
        conversoes_filtradas = conversoes_total[conversoes_total[coluna_id_referencia] == id_campanha_real]
    else:
        conversoes_filtradas = conversoes_total[conversoes_total['customerid'].isin(
            clientes_impactados)]
else:
    # Caso não exista campaignid, filtramos a tabela de conversões pelos clientes que receberam esta campanha
    conversoes_filtradas = conversoes_total[conversoes_total['customerid'].isin(
        clientes_impactados)]

clientes_convertidos = set(conversoes_filtradas['customerid'].dropna().unique())
intersecao_campanha_pedido = len(clientes_impactados.intersection(clientes_convertidos))
taxa_conversao = (len(clientes_convertidos) / len(clientes_impactados) * 100) if len(clientes_impactados) > 0 else 0

data_lancamento = dados_campanha_focada['sendat'].min()

# Verificar se a campanha possui data válida antes de prosseguir
if not pd.isna(data_lancamento):
#-----------------------------------------------------------------------------------------------------------------------
    janela_anterior = (pedidos_loja['createdat'] >= data_lancamento -
                     pd.Timedelta(days=7)) & (pedidos_loja['createdat'] < data_lancamento)
    janela_posterior = (pedidos_loja['createdat'] >= data_lancamento) & (
        pedidos_loja['createdat'] <= data_lancamento + pd.Timedelta(days=7))

    receita_antes = pedidos_loja.loc[janela_anterior, 'totalamount'].sum()
    receita_depois = pedidos_loja.loc[janela_posterior, 'totalamount'].sum()
    variacao_percentual = ((receita_depois - receita_antes) / receita_antes) * \
        100 if receita_antes != 0 else 0

    col1, col2, col3 = st.columns(3)

    col1.metric("Clientes que receberam a campanha", len(clientes_impactados))#clientes que receberam a campanha
    col2.metric("Clientes convertidos", len(clientes_convertidos)) #clientes que realmente converteram
    col3.metric("Taxa de Conversão", f"{taxa_conversao:.2f}%")#taxa de conversão

    st.markdown("---")

    col4, col5, col6 = st.columns(3)
    col4.metric("Data de Lançamento", data_lancamento.strftime('%d/%m/%Y'))
    col5.metric("Receita (7 dias Antes)", f"R$ {receita_antes:,.2f}")
    col6.metric("Receita (7 dias Depois)", f"R$ {receita_depois:,.2f}", delta=f"{variacao_percentual:.2f}%")

    st.markdown("---")

#-----------------------------------------------------------------------------------------------------------------------

    st.subheader("Evolução Diária (Janela de 20 dias)")
    df_receita_diaria = pedidos_loja.copy()
    df_receita_diaria['data'] = df_receita_diaria['createdat'].dt.date
    receita_diaria_agrupada = df_receita_diaria.groupby(
        'data')['totalamount'].sum().reset_index()
    receita_diaria_agrupada['data'] = pd.to_datetime(
        receita_diaria_agrupada['data']).dt.tz_localize('UTC')

    # Definir a data de início como 10 dias antes do lançamento da campanha
    data_inicio_grafico = data_lancamento - pd.Timedelta(days=10)
    # Definir a data de fim como 10 dias depois do lançamento da campanha
    data_fim_grafico = data_lancamento + pd.Timedelta(days=10)

    # Criar uma máscara para filtrar os dados dentro da janela de 20 dias em torno do lançamento da campanha
    mascara_janela = (receita_diaria_agrupada['data'] >= data_inicio_grafico) & (
        receita_diaria_agrupada['data'] <= data_fim_grafico)
    # Filtrar os dados usando a máscara e criar uma cópia para evitar o SettingWithCopyWarning
    dados_grafico_filtrados = receita_diaria_agrupada.loc[mascara_janela].copy()
    # Criar uma nova coluna com a data formatada como string para exibição no gráfico
    dados_grafico_filtrados['data_formatada'] = dados_grafico_filtrados['data'].dt.strftime('%d/%m')

    grafico_evolucao = alt.Chart(dados_grafico_filtrados).mark_bar(
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color="#491a13", offset=0),
                   alt.GradientStop(color='#913322', offset=1)],
            x1=1,  # Inverter a direção do gradiente para que o mais escuro fique no topo
            x2=1,  # Manter a direção vertical
            y1=1,  # Inverter a direção do gradiente para que o mais escuro fique no topo
            y2=0.3  # Manter a direção vertical
        ),
        cornerRadius=25,
    ).encode(
        # Manter a ordem cronológica
        x=alt.X('data_formatada:N', title='Data', sort=None),
        y=alt.Y('totalamount:Q', title='Receita Total')
    ).properties(height=400)

    st.altair_chart(grafico_evolucao, use_container_width=True)

#-----------------------------------------------------------------------------------------------------------------------
else:
    st.warning("Data de lançamento não disponível para a campanha selecionada.")
import streamlit as st
import numpy as np
import pandas as pd
import os
import altair as alt
from openai import OpenAI

st.set_page_config(page_title="Análise de Performance", layout="wide")

# CSS atualizado com Navbar
st.markdown("""
    <style>
    .stApp { 
        background-color: #FFE8E8; 
    }
    /* Estilização da Navbar */
    .nav-container {
        display: flex;
        align-items: center;
        background-color: #913322;
        padding: 1rem 2rem;
        border-radius: 0 0 2rem 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .nav-text {
        color: white;
        font-weight: 900;
        text-transform: uppercase;
        font-family: 'Montserrat', sans-serif;
        font-size: 1.8rem;
        margin-left: 1.5rem;
    }
    [data-testid="stMetric"] {
        display: flex;
        background-color: #B04735;
        color: #fff;
        padding: 15px;
        border-radius: 2rem;
        height: 125px;
        border: 1px solid #e0e0e06c;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        justify-content: center;
        align-items: center;
        text-align: center;
        transition: transform 0.2s;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
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
        color: #F2E0A5;
        font-size: 14px;
        font-weight: bold;
    }
    [data-baseweb="select"] > div {
        border-radius: 2rem;
        border: 1px solid #00000062;
        text-align: center;
        font-size: 20px;
        font-weight: bold;
        color: #565656FF;
        margin-bottom: 20px;
    }
    label[data-testid="stWidgetLabel"] p {
        color: #913322 !important;
        font-weight: bold;
    }
    .ia-insight-box {
        background-color: #ffffff;
        border-left: 5px solid #913322;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        color: #31333F;
    }
    </style>
    """, unsafe_allow_html=True)

with st.container():
    col_logo, col_titulo = st.columns([1, 5])

    with col_logo:
        st.image("Logo.svg", width=120)

    with col_titulo:
        st.markdown('<p class="nav-text" style="color: #913322; font-weight: 900; text-transform: uppercase; font-family: \'Montserrat\', sans-serif; font-size: 1.8rem; margin-left: 1.5rem; margin-top: 20px">Análise de Performance das Campanhas</p>', unsafe_allow_html=True)


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def obter_insight_ia(nome_camp, metricas):
    try:
        client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=st.secrets["GROQ_API_KEY"]
        )

        prompt = f"""
        Analise a campanha '{nome_camp}':
        - Clientes Impactados: {metricas['impactados']}
        - Taxa de Conversão: {metricas['conversao']:.2f}%
        - Receita Gerada Diretamente: {formatar_moeda(metricas['receita_direta'])}
        Gere uma análise executiva curta e estratégica.
        """

        resposta = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"Erro técnico: {str(e)}"


@st.cache_data
def carregar_dados():
    df_campanhas = pd.read_csv('../data/CAMPAIGN.CSV')
    df_conversoes = pd.read_csv('../data/CAMPAIGNxORDER.CSV')
    df_pedidos_loja = pd.read_csv('../data/STOREORDER.csv')
    df_stores = pd.read_csv('../data/STORE.CSV')

    col_id_store = next((c for c in [
                        'id', 'storeid', 'STOREID'] if c in df_stores.columns), df_stores.columns[0])
    col_nome_store = next((c for c in ['nome_store', 'nomestore', 'NOME_STORE',
                          'name', 'nome'] if c in df_stores.columns), df_stores.columns[1])

    mapa_lojas = df_stores.set_index(col_id_store)[col_nome_store].to_dict()

    return df_campanhas, df_conversoes, df_pedidos_loja, mapa_lojas


campanhas_total, conversoes_total, pedidos_loja, mapa_lojas = carregar_dados()

campanhas_total['sendat'] = pd.to_datetime(
    campanhas_total['sendat'], errors='coerce', utc=True)
pedidos_loja['createdat'] = pd.to_datetime(
    pedidos_loja['createdat'], errors='coerce', utc=True)

lista_campanhas = sorted(campanhas_total['name'].unique())
campanha_selecionada = st.selectbox(
    "Selecione a Campanha para análise:", lista_campanhas)


dados_campanha_focada = campanhas_total[campanhas_total['name']
                                        == campanha_selecionada]

id_loja_campanha = dados_campanha_focada['storeid'].iloc[
    0] if 'storeid' in dados_campanha_focada.columns else None
nome_loja_atual = mapa_lojas.get(id_loja_campanha, f"Loja {id_loja_campanha}")

clientes_impactados = set(
    dados_campanha_focada['customerid'].dropna().unique())

conversoes_vinculadas = conversoes_total[conversoes_total['customerid'].isin(
    clientes_impactados)]

if id_loja_campanha is not None and 'storeid' in conversoes_vinculadas.columns:
    conversoes_vinculadas = conversoes_vinculadas[conversoes_vinculadas['storeid']
                                                  == id_loja_campanha]

col_order_id = next((c for c in ['order_id', 'orderid', 'ORDERID',
                    'id_pedido'] if c in conversoes_vinculadas.columns), None)
col_store_id_pedidos = next(
    (c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)

if col_order_id:
    pedidos_convertidos = pedidos_loja[pedidos_loja['id'].isin(
        conversoes_vinculadas[col_order_id])]
else:
    pedidos_convertidos = pd.DataFrame()

if id_loja_campanha is not None and col_store_id_pedidos:
    pedidos_convertidos = pedidos_convertidos[pedidos_convertidos[col_store_id_pedidos]
                                              == id_loja_campanha]

clientes_convertidos = set(pedidos_convertidos['customerid'].unique(
)) if not pedidos_convertidos.empty else set()
taxa_conversao = (len(clientes_convertidos) / len(clientes_impactados)
                  * 100) if len(clientes_impactados) > 0 else 0
receita_direta = pedidos_convertidos['totalamount'].sum(
) if not pedidos_convertidos.empty else 0

data_lancamento = dados_campanha_focada['sendat'].min()

if not pd.isna(data_lancamento):
    janela_anterior = (pedidos_loja['createdat'] >= data_lancamento - pd.Timedelta(
        days=7)) & (pedidos_loja['createdat'] < data_lancamento)
    janela_posterior = (pedidos_loja['createdat'] >= data_lancamento) & (
        pedidos_loja['createdat'] <= data_lancamento + pd.Timedelta(days=7))

    if col_store_id_pedidos:
        receita_loja_antes = pedidos_loja.loc[janela_anterior & (
            pedidos_loja[col_store_id_pedidos] == id_loja_campanha), 'totalamount'].sum()
        receita_loja_depois = pedidos_loja.loc[janela_posterior & (
            pedidos_loja[col_store_id_pedidos] == id_loja_campanha), 'totalamount'].sum()
    else:
        receita_loja_antes = pedidos_loja.loc[janela_anterior, 'totalamount'].sum(
        )
        receita_loja_depois = pedidos_loja.loc[janela_posterior, 'totalamount'].sum(
        )

    variacao_loja = receita_loja_depois - receita_loja_antes
    porcentagem_variacao = (
        variacao_loja / receita_loja_antes * 100) if receita_loja_antes > 0 else 0

    # st.info(f"📍 Unidade Responsável: **{nome_loja_atual}**")

    col1, col2, col3 = st.columns(3)
    col1.metric("Clientes Impactados",
                f"{len(clientes_impactados):,}".replace(",", "."))
    col2.metric("Clientes Convertidos",
                f"{len(clientes_convertidos):,}".replace(",", "."))
    col3.metric("Taxa de Conversão",
                f"{taxa_conversao:.2f}%".replace(".", ","))

    st.markdown("---")

    col4, col5, col6 = st.columns(3)
    col4.metric("Data de Lançamento", data_lancamento.strftime('%d/%m/%Y'))
    col5.metric("Receita Direta Campanha", formatar_moeda(receita_direta))
    col6.metric("Performance Total da Loja", f"{porcentagem_variacao:.2f}%".replace(
        ".", ","), delta=formatar_moeda(variacao_loja))

    st.subheader(f"Evolução Diária da Receita - {nome_loja_atual}")
    df_receita_diaria = pedidos_loja.copy()
    if col_store_id_pedidos:
        df_receita_diaria = df_receita_diaria[df_receita_diaria[col_store_id_pedidos]
                                              == id_loja_campanha]

    df_receita_diaria['data'] = df_receita_diaria['createdat'].dt.date
    receita_diaria_agrupada = df_receita_diaria.groupby(
        'data')['totalamount'].sum().reset_index()
    receita_diaria_agrupada['data'] = pd.to_datetime(
        receita_diaria_agrupada['data']).dt.tz_localize('UTC')

    data_inicio_grafico = data_lancamento - pd.Timedelta(days=7)
    data_fim_grafico = data_lancamento + pd.Timedelta(days=7)

    mascara_janela = (receita_diaria_agrupada['data'] >= data_inicio_grafico) & (
        receita_diaria_agrupada['data'] <= data_fim_grafico)
    dados_grafico_filtrados = receita_diaria_agrupada.loc[mascara_janela].copy(
    )
    dados_grafico_filtrados['data_formatada'] = dados_grafico_filtrados['data'].dt.strftime(
        '%d/%m')

    grafico_evolucao = alt.Chart(dados_grafico_filtrados).mark_bar(
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color="#491a13", offset=0),
                   alt.GradientStop(color='#913322', offset=1)],
            x1=1, x2=1, y1=1, y2=0.3
        ),
        cornerRadius=25,
    ).encode(
        x=alt.X('data_formatada:N', title='Data', sort=None),
        y=alt.Y('totalamount:Q', title='Receita Total')
    ).properties(height=400)

    st.altair_chart(grafico_evolucao, use_container_width=True)

else:
    st.warning("Data de lançamento não disponível para a campanha selecionada.")

st.markdown("---")

if st.button("Gerar Análise com IA"):
    with st.spinner('Analisando...'):
        resumo = {
            'impactados': len(clientes_impactados),
            'conversao': taxa_conversao,
            'receita_direta': receita_direta,
            'crescimento': porcentagem_variacao
        }
        st.markdown(
            f'<div class="ia-insight-box">💡 <b>Insight:</b><br>{obter_insight_ia(campanha_selecionada, resumo)}</div>', unsafe_allow_html=True)

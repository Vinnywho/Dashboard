import streamlit as st
import numpy as np
import pandas as pd
import os
import altair as alt
import polars as pl
import random
from random import randint
from streamlit_echarts import st_echarts, JsCode
from openai import OpenAI

def configurar_interface():
    st.set_page_config(page_title="Cannolitsky", layout="wide", page_icon="Logo.svg")
    st.markdown("""
        <style>
        .stApp { 
            background-color: #FCF8F8; 
        }
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
        [data-testid="column"] {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-content: center;
            align-items: center;
            text-align: center;
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

    mapa_lojas = dict(zip(df_stores['id'], df_stores['name']))

    for df, col in [(df_campanhas, 'sendat'), (df_pedidos_loja, 'createdat')]:
        df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
    df_pedidos_loja['scheduledat'] = pd.to_datetime(df_pedidos_loja['scheduledat'], format='mixed')

    return df_campanhas, df_conversoes, df_pedidos_loja, mapa_lojas

def grafico_porcentagem(titulo, porcentagem):
    options = {
                "title": {
                "text": titulo,
                "left": "center",
                "top" : "5px",
                "textStyle": {"color": "#913322", "fontSize": 18}
            },
            "series": [
                {
                    "type": "gauge",
                    "progress": {
                        "show": True, 
                        "width": 13,
                        "itemStyle": {"color": "#913322"}
                    },
                    "axisLine": {"lineStyle": {"width": 13}},
                    "axisTick": {"show": False},
                    "splitLine": {"length": 7, "lineStyle": {"width": 1, "color": "#999"}},
                    "axisLabel": {"distance": 19, "color": "#999", "fontSize": 12},
                    "anchor": {
                        "show": True,
                        "showAbove": True,
                        "size": 15,
                        "itemStyle": {
                            "borderWidth": 10,
                            "borderColor": "#913322",
                        },
                    },
                    "pointer": {
                        "itemStyle": {"color": "#913322"}
                    },
                    "title": {"show": True},
                    "detail": {
                        "valueAnimation": True,
                        "fontSize": 30,
                        "offsetCenter": [0, "70%"],
                        "formatter": "{value}%",
                    },
                    "data": [{"value": porcentagem}],
                }
            ]
        }
    return st_echarts(options=options, height="300px")

def grafico_de_4_variaveis(dataframe):
    chart_barras = alt.Chart(dataframe).mark_bar(cornerRadius=25).encode(
        x=alt.X('Categoria:N', title='Componentes da Receita', sort='-y'),
        y=alt.Y('Valor:Q', title='Valor (R$)'),
        color=alt.Color('Categoria:N', scale=alt.Scale(range=['#913322', '#B04735', '#491a13', '#F2E0A5'])),
        tooltip=[alt.Tooltip('Categoria', title='Componente'), alt.Tooltip('Valor', title='Valor', format=',.2f')]
    ).properties(height=400)
    return st.altair_chart(chart_barras, use_container_width=True)

def grafico_pizza(titulo, df):
    dados_formatados = [
        {"value": row['Valor'], "name": row['Categoria']} 
        for _, row in df.iterrows()
    ]

    options = {
        "title": {
                "text": titulo,
                "left": "center",
                "top" : "5px",
                "textStyle": {"color": "#913322", "fontSize": 18}
            },
        "tooltip": {"trigger": "item"},
        "legend": {"top": "5%", "left": "center"},
        "color": ["#913322", "#F2E0A5", "#491a13"],
        "series": [
            {
                "name": "Valor",
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2,
                },
                "label": {"show": False, "position": "center"},
                "emphasis": {
                    "label": {"show": True, "fontSize": 20, "fontWeight": "bold"}
                },
                "labelLine": {"show": False},
                "data": dados_formatados,
            }
        ],
    }
    return st_echarts(options=options, height="500px")

def grafico_semi_circulo(titulo, df):
    dados_echarts = [
        {"value": float(row['Valor']), "name": row['Categoria']} 
        for _, row in df.iterrows()
    ]
    
    options = {
        "title": {
            "text": titulo,
            "left": "center",
            "top" : "5px",
            "textStyle": {"color": "#913322", "fontSize": 18}
        },
        "tooltip": {"trigger": "item"},
        "legend": {"top": "15%", "left": "center"},
        "color": ["#913322", "#F2E0A5"],
        "series": [
            {
                "name": "Ticket Médio",
                "type": "pie",
                "radius": ["40%", "70%"],
                "center": ["50%", "75%"],
                "startAngle": 180,
                "endAngle": 360,
                "avoidLabelOverlap": False,
                "label": {"show": True, "position": "inside", "formatter": "{c}"},
                "data": dados_echarts,
            }
        ],
    }
    return st_echarts(options=options, height="400px")

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

def renderizar_tab_campanhas_loja(impactados, pedidos_convertidos, id_loja_campanha, nome_loja_atual, col_store_id_pedidos, campanhas_total, campanha_selecionada, pedidos_loja):
    clientes_convertidos = set(pedidos_convertidos['customerid'].unique()) if not pedidos_convertidos.empty else set()
    taxa_conversao = (len(clientes_convertidos) / len(impactados) * 100) if len(impactados) > 0 else 0
    receita_direta = pedidos_convertidos['totalamount'].sum() if not pedidos_convertidos.empty else 0

    data_lancamento = campanhas_total[campanhas_total['name'] == campanha_selecionada]['sendat'].min()

    if not pd.isna(data_lancamento):
        janela_anterior = (pedidos_loja['createdat'] >= data_lancamento - pd.Timedelta(days=7)) & (pedidos_loja['createdat'] < data_lancamento)
        janela_posterior = (pedidos_loja['createdat'] >= data_lancamento) & (pedidos_loja['createdat'] <= data_lancamento + pd.Timedelta(days=7))

        if col_store_id_pedidos:
            rec_antes = pedidos_loja.loc[janela_anterior & (pedidos_loja[col_store_id_pedidos] == id_loja_campanha), 'totalamount'].sum()
            rec_depois = pedidos_loja.loc[janela_posterior & (pedidos_loja[col_store_id_pedidos] == id_loja_campanha), 'totalamount'].sum()
        else:
            rec_antes = pedidos_loja.loc[janela_anterior, 'totalamount'].sum()
            rec_depois = pedidos_loja.loc[janela_posterior, 'totalamount'].sum()

        variacao_loja = rec_depois - rec_antes
        porcentagem_variacao = (variacao_loja / rec_antes * 100) if rec_antes > 0 else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Clientes Impactados", f"{len(impactados):,}".replace(",", "."))
        col2.metric("Clientes Convertidos", f"{len(clientes_convertidos):,}".replace(",", "."))
        col3.metric("Taxa de Conversão", f"{taxa_conversao:.2f}%".replace(".", ","))

        st.markdown("---")

        col4, col5, col6 = st.columns(3)
        col4.metric("Data de Lançamento", data_lancamento.strftime('%d/%m/%Y'))
        col5.metric("Receita Direta Campanha", formatar_moeda(receita_direta))
        col6.metric("Performance Total da Loja", f"{porcentagem_variacao:.2f}%".replace(".", ","), delta=formatar_moeda(variacao_loja))

        st.subheader(f"Evolução Diária da Receita - {nome_loja_atual}")
        df_receita_diaria = pedidos_loja.copy()
        if col_store_id_pedidos:
            df_receita_diaria = df_receita_diaria[df_receita_diaria[col_store_id_pedidos] == id_loja_campanha]

        df_receita_diaria['data'] = df_receita_diaria['createdat'].dt.date
        rec_agrupada = df_receita_diaria.groupby('data')['totalamount'].sum().reset_index()
        rec_agrupada['data'] = pd.to_datetime(rec_agrupada['data']).dt.tz_localize('UTC')

        mask = (rec_agrupada['data'] >= data_lancamento - pd.Timedelta(days=7)) & (rec_agrupada['data'] <= data_lancamento + pd.Timedelta(days=7))
        dados_grafico = rec_agrupada.loc[mask].copy()
        dados_grafico['data_formatada'] = dados_grafico['data'].dt.strftime('%d/%m')

        grafico = alt.Chart(dados_grafico).mark_bar(
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color="#491a13", offset=0), alt.GradientStop(color='#913322', offset=1)],
                x1=1, x2=1, y1=1, y2=0.3
            ),
            cornerRadius=25,
        ).encode(
            x=alt.X('data_formatada:N', title='Data', sort=None),
            y=alt.Y('totalamount:Q', title='Receita Total')
        ).properties(height=400)

        st.altair_chart(grafico, use_container_width=True)
        return taxa_conversao, receita_direta
    else:
        st.warning("Data de lançamento não disponível para a campanha selecionada.")
        return 0, 0

def renderizar_tab_visao_geral(pedidos_loja, col_store_id_pedidos, mapa_lojas):
    st.subheader("Visão Geral - Todas as Lojas")
    receita_total = pedidos_loja['totalamount'].sum()
    ticket_medio_geral = pedidos_loja['totalamount'].mean()
    
    col9, col10 = st.columns(2)
    col9.metric("Receita Total", formatar_moeda(receita_total))
    col10.metric("Ticket Médio Geral", formatar_moeda(ticket_medio_geral))

    faturamento_lojas = (
        pedidos_loja
        .groupby('nome_loja', as_index=False)['totalamount']
        .sum()
        .sort_values(by='totalamount', ascending=False)
        .head(15)
    ) 

    st.subheader("Faturamento Top 15 Lojas")
    col_pizza, col_info = st.columns([2, 1])

    with col_pizza:
        chart_pizza = alt.Chart(faturamento_lojas).mark_arc(innerRadius=90).encode(
            theta=alt.Theta(field="totalamount", type="quantitative"),
            color=alt.Color(field="nome_loja", type="nominal", legend=alt.Legend(title="Lojas")),
            tooltip=[alt.Tooltip('nome_loja', title='Loja'), alt.Tooltip('totalamount', title='Faturamento', format='.2f')]
        ).properties(height=400)
        st.altair_chart(chart_pizza, use_container_width=True)
    with col_info:
        st.markdown("### Insights Gerais")
        st.markdown(f"A loja com maior faturamento é **{faturamento_lojas.iloc[0]['nome_loja']}** com um total de **{formatar_moeda(faturamento_lojas.iloc[0]['totalamount'])}**.")
        st.markdown(f"A média de faturamento entre as top 15 lojas é de **{formatar_moeda(faturamento_lojas['totalamount'].mean())}**.")
        st.markdown(f"A loja com o menor faturamento é **{faturamento_lojas.iloc[-1]['nome_loja']}** com um total de **{formatar_moeda(faturamento_lojas.iloc[-1]['totalamount'])}**.")
        st.markdown("A distribuição de faturamento mostra que algumas lojas têm um desempenho significativamente melhor do que outras, indicando oportunidades para análise de estratégias e práticas adotadas por essas lojas de destaque.")

    st.markdown("---")
    st.subheader("Pedidos por canal de venda")

    pedidos_canal = pedidos_loja['saleschannel'].value_counts().reset_index()

    chart_barras = alt.Chart(pedidos_canal).mark_bar().encode(
        x=alt.X('saleschannel:N', title='Canal de Venda', sort='-y'),
        y=alt.Y('count:Q', title='Quantidade de Pedidos'),
        color=alt.Color('saleschannel:N'),
        tooltip=[alt.Tooltip('saleschannel', title='Canal de Venda'), alt.Tooltip('count', title='Quantidade de Pedidos')]
    ).properties(height=400)

    st.altair_chart(chart_barras, use_container_width=True)

def renderizar_tab_testes(pedidos_loja, status_16, col_store_id_pedidos, col_store_name, mapa_lojas, conversoes_total):
    st.subheader("Testes de Cálculos e Métricas")
    st.markdown("Aqui você pode realizar testes rápidos de cálculos ou métricas específicas relacionadas às campanhas ou lojas. Insira os valores desejados para obter resultados instantâneos.")

    with st.expander("1 - Estrutura da Receita", expanded=True):
        st.subheader("Indice 1.1 - Decomposição da Receita Reportada")
        receita_status_16 = status_16['subtotalamount'].sum()
        total_descontos = status_16['discountamount'].sum()
        total_taxas = status_16['taxamount'].sum()
        receita_total = status_16['totalamount'].sum()

        col_grafico_1_1, cards_1_1 = st.columns([2, 1])

        with col_grafico_1_1:
            dados_grafico = pd.DataFrame({
                'Categoria': ['Subtotal', 'Descontos', 'Taxas', 'Receita Total'],
                'Valor': [receita_status_16, total_descontos, total_taxas, receita_total]
            })
            grafico_de_4_variaveis(dados_grafico)

        with cards_1_1:
            pct_receita = (receita_status_16 / receita_total * 100) if receita_total > 0 else 0
            pct_taxas = (total_taxas / receita_total * 100) if receita_total > 0 else 0
            
            st.metric(label="Total de Receita", value=f"{pct_receita:.2f}%")
            st.metric(label="Sobre Taxas (Status 16)", value=f"{pct_taxas:.2f}%")
        st.markdown("---")



        st.subheader("Índice 1.2 - Receita Líquida Comercial")
        col1, col2 = st.columns(2)
        col1.metric("Receita Líquida Comercial", formatar_moeda(receita_status_16 - (status_16['discountamount'].sum())))
        col2.metric("Taxa de Desconto", f"{status_16['discountamount'].sum() / status_16['subtotalamount'].sum() * 100:.2f}%")
        # st.markdown(f"*Receita líquida comercial:** {formatar_moeda(receita_status_16 - (status_16['discountamount'].sum()))}")
        # st.markdown(f"**Taxa de desconto sobre subtotal:** {status_16['discountamount'].sum() / status_16['subtotalamount'].sum() * 100:.2f}%")
        st.markdown("---")



        st.subheader("Índice 1.3 - Taxa de Realização da Receita")
        col3, col4, col5 = st.columns(3)
        col3.metric("**Receita potencial:**", f"{len(pedidos_loja) * status_16['totalamount'].mean():,.2f}".replace(",", "."))
        col4.metric("**Receita realizada:**", f"{formatar_moeda(status_16['totalamount'].sum())}")
        col5.metric(f"**Índice de realização:**", f"{status_16['totalamount'].sum() / (len(pedidos_loja) * status_16['totalamount'].mean()) * 100:.2f}%")
        st.markdown("---")



        st.subheader("Índice 1.4 - Custo de Oportunidade dos Não-Concluídos")
        col6, col7, col8 = st.columns(3)
        col6.metric("**Pedidos não concluidos:**", f"{len(pedidos_loja) - len(status_16)}")
        col7.metric("**Receita não realizada:**", f"{formatar_moeda((len(pedidos_loja) - len(status_16)) * status_16['totalamount'].mean())}")
        col8.metric("**Porcentagem de receita não realizada:**", f"{(len(pedidos_loja) - len(status_16)) * status_16['totalamount'].mean() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown("---")



    with st.expander("2 - Cancelamento e Qualidade"):


        st.subheader("Índice 2.1 - Taxa de Cancelamento Efetivo")
        cancelados_8 = pedidos_loja[pedidos_loja['status'] == 8]
        cancelados_11 = pedidos_loja[pedidos_loja['status'] == 11]
        cancelados_14 = pedidos_loja[pedidos_loja['status'] == 14]
        cancelados = pd.concat([cancelados_8, cancelados_11, cancelados_14])
        taxa_cancelamento = f"{len(cancelados) / len(pedidos_loja) * 100:.2f}"
        st.metric("**Pedidos cancelados:**", f"{len(cancelados)}")
        # st.markdown(f"**Taxa de cancelamento:** {taxa_cancelamento}%")
        grafico_porcentagem("Taxa de Cancelamento", taxa_cancelamento)
        st.markdown("---")



        st.subheader("Índice 2.2 - Decomposição do Cancelamento por Origem")
        # col9, col10 = st.columns(2)
        cancelados_por_estabeleceimento = f"{len(cancelados_8) / len(pedidos_loja) * 100:.2f}"
        cancelados_por_cliente = f"{len(cancelados_11) / len(pedidos_loja) * 100:.2f}"
        cancelados_por_timeout = f"{len(cancelados_14) / len(pedidos_loja) * 100:.2f}"
        soma_cancelados = f"{len(cancelados) / len(pedidos_loja) * 100:.2f}"
        dados_grafico2_2 = pd.DataFrame({
                'Categoria': ['Cancelados por estabelecimento', 'Cancelados por cliente', 'Expirados/timeout', 'Soma das tres causas'],
                'Valor': [cancelados_por_estabeleceimento, cancelados_por_cliente, cancelados_por_timeout, soma_cancelados]})
        grafico_de_4_variaveis(dados_grafico2_2)
        # with col9:
        #     st.metric(f"**Cancelados por estabelecimento:**",f" {cancelados_por_estabeleceimento}%")
        #     st.metric(f"**Expirados/timeout:**",f" {cancelados_por_timeout}%")
        # with col10:
        #     st.metric(f"**Cancelados por cliente:**",f" {cancelados_por_cliente}%")
        #     st.metric(f"**Soma das tres causas:**",f" {soma_cancelados}%")
        st.markdown("---")



        st.subheader("Índice 2.3 - Receita Perdida por Cancelamento Efetivo")
        col11, col12 = st.columns(2)
        receita_perdida_por_cancelamento = f"{formatar_moeda(len(cancelados) * status_16['totalamount'].mean())}"
        porcentagem_perdida_cancelamento = f"{(len(cancelados) * status_16['totalamount'].mean()) / status_16['totalamount'].sum() * 100:.2f}"
        with col11:
            col11.metric(f"**Cancelados:**",f" {len(cancelados)}")
            col11.metric(f"**Receita perdida por cancelamento:**",f" {receita_perdida_por_cancelamento}")
        with col12:
            grafico_porcentagem("Porcentagem de receita perdida por cancelamento", porcentagem_perdida_cancelamento)
        st.markdown("---")



    with st.expander("3 - Eficiência e Produtividade"):


        st.subheader("Índice 3.1 - Taxa de Ativação de Lojas")
        col14, col15 = st.columns(2)
        total_lojas_cadastradas = len(mapa_lojas)
        with col14:
            st.markdown(f"<div style='color: #913322; font-size: 18px; font-weight: bold;'>Lojas cadastradas: {total_lojas_cadastradas} </div>", unsafe_allow_html=True)
            st.dataframe(mapa_lojas, use_container_width=True, hide_index=True)

        ids_lojas_ativas = pedidos_loja[col_store_id_pedidos].unique() if col_store_id_pedidos else []

        lista_lojas_ativas = {id: nome for id, nome in mapa_lojas.items() if id in ids_lojas_ativas}
        with col15:
            st.markdown(f"<div style='color: #913322; font-size: 18px; font-weight: bold;'>Lojas ativas: {len(lista_lojas_ativas)} </div>", unsafe_allow_html=True)
            st.dataframe(lista_lojas_ativas, use_container_width=True, hide_index=True)

        if total_lojas_cadastradas > 0:
            lojas_ativas_count = len(lista_lojas_ativas)
            taxa_inativacao = f"{(lojas_ativas_count / total_lojas_cadastradas) * 100:.2f}"
        else:
            taxa_inativacao = 0

        grafico_porcentagem("Taxa de inativação", taxa_inativacao)
        st.markdown("---")

        st.subheader("Índice 3.2 - Receita Média por Loja Ativa")
        col16, col17 = st.columns(2)
        col16.metric("Receita por Loja Ativa:", f"{formatar_moeda(status_16['totalamount'].sum() / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0))}")
        col17.metric("Receita Mensal Média/Loja:", f"{formatar_moeda(status_16['totalamount'].sum() / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0) / 9)}")
        st.markdown("---")


        st.subheader("Índice 3.3 - Receita Média Diária da Operação")
        data_min = pedidos_loja['createdat'].min()
        data_max = pedidos_loja['createdat'].max()
        periodo_dias = (data_max - data_min).days + 1
        
        receita_total_status_16 = status_16['totalamount'].sum()
        pedidos_total_status_16 = len(status_16)

        col_metric1, col_metric2, col_metric3 = st.columns(3)
        col_metric1.metric("Período Analisado", f"{periodo_dias} dias")
        col_metric2.metric("Receita Média/Dia", formatar_moeda(receita_total_status_16 / periodo_dias))
        col_metric3.metric("Pedidos Médios/Dia", f"{pedidos_total_status_16 / periodo_dias:.2f}")

        #gráfico de calendário com heatmap
        df_heatmap = status_16.copy()
        df_heatmap['data_simples'] = df_heatmap['createdat'].dt.strftime('%Y-%m-%d')
        dados_agrupados = df_heatmap.groupby('data_simples')['totalamount'].sum().reset_index()

        data_heatmap = dados_agrupados.values.tolist()

        ano_analise = data_min.year
        valor_maximo = dados_agrupados['totalamount'].max() if not dados_agrupados.empty else 1000

        option_heatmap = {
            "title": {"top": 30, "left": "center", "text": "Valores de Receita Diária"},
            "tooltip": {
                "formatter": JsCode("""
                    function (p) {
                        return p.data[0] + ': R$ ' + p.data[1].toLocaleString('pt-BR', {minimumFractionDigits: 2});
                    }
                """)
            },
            "visualMap": {
                "min": 0,
                "max": valor_maximo,
                "type": "continuous",
                "orient": "horizontal",
                "left": "center",
                "top": 50,
                "inRange": {"color": ["#F2E0A5", "#B04735", "#913322"]}
            },
            "calendar": {
                "top": 120,
                "left": 30,
                "right": 30,
                "cellSize": ["auto", 20],
                "range": str(ano_analise),
                "itemStyle": {"borderWidth": 0.5},
                "yearLabel": {"show": True},
                "dayLabel": {"nameMap": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]},
                "monthLabel": {"nameMap": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]}
            },
            "series": {
                "type": "heatmap",
                "coordinateSystem": "calendar",
                "data": data_heatmap
            }
        }

        st_echarts(option_heatmap, height="350px", key="heatmap_operacao")
        st.markdown("---")



        st.subheader("Índice 3.4 - Volume Médio por Loja Ativa")
        col18, col19 = st.columns(2)
        col18.metric(f"Pedidos por loja ativa",f" {len(status_16) / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0):.2f}")
        col19.metric(f"Pedidos/Loja/Mês", f"{len(status_16) / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0) / 9:.2f}")
        st.markdown("---")



        st.subheader("Índice 3.5 - ARPU — Receita Média por Cliente")
        col20, col21 = st.columns(2)
        col20.metric(f"Cliente com pedido com status 16",f"{status_16['customerid'].nunique() if status_16['customerid'].nunique() > 0 else 0}")
        arpu = status_16['totalamount'].sum() / status_16['customerid'].nunique() if status_16['customerid'].nunique() > 0 else 0
        col21.metric(f"ARPU", f"{formatar_moeda(arpu)}")
        st.markdown("---")



    with st.expander("4 - Concentração e Risco"):


        st.subheader("Índice 4.1 - HHI — Concentração por Canal de Venda")
        receita_total_calc = status_16['totalamount'].sum()
        # st.markdown(f"**Receita Total:** {formatar_moeda(receita_total_calc)}")
        receita_por_canal = status_16.groupby('saleschannel')['totalamount'].sum()
        shares_receita = receita_por_canal / receita_total_calc
        hhi_total_receita = ((shares_receita**2).sum()) * 10000
        canal_selecionado = st.selectbox("**Canal de venda:**", status_16['saleschannel'].unique())
        receita_canal_selecionado = status_16[status_16['saleschannel'] == canal_selecionado]['totalamount'].sum()
        share_receita_canal = (receita_canal_selecionado / receita_total_calc) * 10000
        st.markdown(f"**Share ({canal_selecionado}):** {share_receita_canal:.2f}")
        share_receita_quadrado = (share_receita_canal / 10000)**2 * 10000
        st.markdown(f"**Share ao quadrado:** {share_receita_quadrado:.2f}") 
        st.markdown(f"**O maior share é**: {shares_receita.max() * 100:.2f}% do {receita_por_canal.idxmax()}")
        st.markdown(f"**HHI Total do Mercado:** {hhi_total_receita:.2f}")
        if hhi_total_receita > 5000:
            st.markdown("<div style='color: #64D248; font-size: 18px; font-weight: bold;'>O mercado é um monopólio</div>", unsafe_allow_html=True)
        elif hhi_total_receita > 2500:
            st.markdown("<div style='color: #ECB92E; font-size: 18px; font-weight: bold;'>O mercado possui alta concentração</div>", unsafe_allow_html=True)
        elif hhi_total_receita > 1500:
            st.markdown("<div style='color: #913322; font-size: 18px; font-weight: bold;'>O mercado está com concentração moderada</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: #D43333; font-size: 18px; font-weight: bold;'>O mercado está desconcentrado</div>", unsafe_allow_html=True)
        st.markdown("---")



        st.subheader("Índice 4.2 - HHI — Concentração por Loja")
        # st.markdown(f"**Receita Total:** {formatar_moeda(receita_total_calc)}")
        receita_por_loja_hhi = status_16.groupby('nome_loja')['totalamount'].sum()
        shares_receita_loja = receita_por_loja_hhi / receita_total_calc
        hhi_total_receita_loja = (shares_receita_loja**2).sum() * 10000
        loja_selecionada = st.selectbox("**Loja:**", sorted(status_16['nome_loja'].unique()))
        receita_loja_selecionada = status_16[status_16['nome_loja'] == loja_selecionada]['totalamount'].sum()
        share_receita_loja = (receita_loja_selecionada / receita_total_calc) * 10000
        st.markdown(f"**Share ({loja_selecionada}):** {share_receita_loja:.2f}")
        share_receita_loja_quadrado = (share_receita_loja / 10000)**2 * 10000
        st.markdown(f"**Share ao quadrado:** {share_receita_loja_quadrado:.2f}")
        maior_loja_nome = receita_por_loja_hhi.idxmax()
        st.markdown(f"**O maior share é**: {shares_receita_loja.max() * 100:.2f}% da loja {maior_loja_nome}")
        st.markdown(f"**HHI Total do Mercado:** {hhi_total_receita_loja:.2f}")
        if hhi_total_receita_loja > 5000:
            st.markdown("<div style='color: #64D248; font-size: 18px; font-weight: bold;'>O mercado é um monopólio</div>", unsafe_allow_html=True)
        elif hhi_total_receita_loja > 2500:
            st.markdown("<div style='color: #ECB92E; font-size: 18px; font-weight: bold;'>O mercado possui alta concentração</div>", unsafe_allow_html=True)
        elif hhi_total_receita_loja > 1500:
            st.markdown("<div style='color: #913322; font-size: 18px; font-weight: bold;'>O mercado está com concentração moderada</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: #D43333; font-size: 18px; font-weight: bold;'>O mercado está desconcentrado</div>", unsafe_allow_html=True)
        st.markdown("---")



        st.subheader("Índice 4.3 - Curva ABC de Receita por Loja")
        receita_por_loja_abc = status_16.groupby('nome_loja')['totalamount'].sum().sort_values(ascending=False)
        receita_total_abc = receita_por_loja_abc.sum()
        shares_abc = receita_por_loja_abc / receita_total_abc
        top_1_val = shares_abc.iloc[0] * 100
        top_4_val = shares_abc.iloc[:4].sum() * 100
        top_10_val = shares_abc.iloc[:10].sum() * 100
        n_lojas_total = len(receita_por_loja_abc)
        n_vinte_pct = int(n_lojas_total * 0.2)
        top_20_pct_val = shares_abc.iloc[:n_vinte_pct].sum() * 100

        dados_grafico4_3 = pd.DataFrame({
                'Categoria': ['Top 1 Loja (Share)', 'Top 4 Lojas (Acumulado)', 'Top 10 Lojas (Acumulado)', 'Top 20% (Lojas):'],
                'Valor': [top_1_val, top_4_val, top_10_val, top_20_pct_val]})
        grafico_de_4_variaveis(dados_grafico4_3)
        
        # st.markdown(f"**Top 1 Loja (Share):** {top_1_val:.2f}%")
        # st.markdown(f"**Top 4 Lojas (Acumulado):** {top_4_val:.2f}%")
        # st.markdown(f"**Top 10 Lojas (Acumulado):** {top_10_val:.2f}%")
        # st.markdown(f"**Top 20% ({n_vinte_pct} Lojas):** {top_20_pct_val:.2f}%")
        st.markdown("---")



        st.subheader("Índice 4.4 - Coeficiente de Gini de Receita por Loja")
        
        valores = np.sort(receita_por_loja_abc.values)
        n = len(valores)
        indices = np.arange(1, n + 1)
        gini = (2 * np.sum(indices * valores)) / (n * np.sum(valores)) - (n + 1) / n
        st.markdown(f"**Gini das lojas**: {gini:.3f}")

        if gini < 0.5:
            st.markdown(f"<div style='color: #64D248; font-size: 18px; font-weight: bold;'>Interpretação: Desigualdade Baixa</div>", unsafe_allow_html=True)
        elif 0.5 <= gini <= 0.7:
            st.markdown(f"<div style='color: #ECB92E; font-size: 18px; font-weight: bold;'>Interpretação: Desigualdade Alta</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color: #D43333; font-size: 18px; font-weight: bold;'>Interpretação: Desigualdade Muito ALta</div>", unsafe_allow_html=True)
        st.markdown("---")



    with st.expander("5 - Indicadores Promocionais"):


        st.subheader("Índice 5.1 - Investimento Promocional como % da Receita")
        st.metric(f"Investimento promocional:", f"{formatar_moeda(status_16['discountamount'].sum())}")
        col22, col23 = st.columns(2)
        porcentagem_sobre_receita = f"{status_16['discountamount'].sum() / status_16['totalamount'].sum() * 100:.2f}"
        porcentagem_sobre_subtotal = f"{status_16['discountamount'].sum() / status_16['subtotalamount'].sum() * 100:.2f}"
        with col22:
            grafico_porcentagem("Porcentagem sobre receita", porcentagem_sobre_receita)
        with col23:
            grafico_porcentagem("Porcentagem sobre subtotal", porcentagem_sobre_subtotal)
        st.markdown("---")



        st.subheader("Índice 5.2 - Profundidade Média do Desconto")
        col24, col25, col26 = st.columns(3)
        col24.metric(f"Pedidos com desconto",f"{len(status_16[status_16['discountamount'] > 0])}")
        col25.metric(f"Subtotal dos beneficiados",f"{formatar_moeda(status_16[status_16['discountamount'] > 0]['subtotalamount'].sum())}")
        col26.metric(f"Desconto absoluto médio",f"{formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean())}")
        porcentagem_pedidos_com_desconto = f"{len(status_16[status_16['discountamount'] > 0]) / len(status_16) * 100:.2f}"
        profundidade_media = f"{status_16['discountamount'].sum() / status_16[status_16['discountamount'] > 0]['subtotalamount'].sum() * 100:.2f}"
        col27, col28 = st.columns(2)
        with col27:
            grafico_porcentagem("Porcentagem de pedidos com desconto", porcentagem_pedidos_com_desconto)
        with col28:
            grafico_porcentagem("Profundidade Média", profundidade_media)
        st.markdown("---")



        st.subheader("Índice 5.3 - Análise de Uplift — Ticket com vs sem Desconto")
        ticket_com_desconto = f"{status_16[status_16['discountamount'] > 0]['totalamount'].mean():.2f}"
        ticket_sem_desconto = f"{status_16[status_16['discountamount'] == 0]['totalamount'].mean():.2f}"
        st.metric(f"Uplift",f"{(status_16[status_16['discountamount'] > 0]['totalamount'].mean() - status_16[status_16['discountamount'] == 0]['totalamount'].mean()) / status_16[status_16['discountamount'] == 0]['totalamount'].mean() * 100:.2f}%")
        dados_grafico5_3 = pd.DataFrame({
                'Categoria': ['Ticket - pedidos com desconto', 'Ticket - pedidos sem desconto'],
                'Valor': [ticket_com_desconto, ticket_sem_desconto]})
        grafico_semi_circulo("Análise de Uplift", dados_grafico5_3)
        
        st.markdown("---")



        st.subheader("Índice 5.4 - Custo Promocional por Pedido Beneficiado")
        custo_pedido_desconto = f"{status_16[status_16['discountamount'] > 0]['discountamount'].mean():.2f}"
        custo_pedido_geral = f"{status_16['discountamount'].mean():.2f}"
        custo_promocional_diluido = f"{status_16[status_16['discountamount'] > 0]['discountamount'].mean() - status_16['discountamount'].mean():.2f}"
        # st.markdown(f"**Custo / Pedido c/ Desconto:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean())}")
        # st.markdown(f"**Custo / Pedido (geral):** {formatar_moeda(status_16['discountamount'].mean())}")
        # st.markdown(f"**Custo promocional diluido:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean() - status_16['discountamount'].mean())}")

        dados_grafico5_4 = pd.DataFrame({
                'Categoria': ['Custo / Pedido c/ Desconto', 'Custo / Pedido (geral)', 'Custo promocional diluido'],
                'Valor': [custo_pedido_desconto, custo_pedido_geral, custo_promocional_diluido]})
        grafico_pizza("Custo Promocional por Pedido Beneficiado (R$)",dados_grafico5_4)
        st.markdown("---")



        st.subheader("Índice 5.5 - Receita Atribuída a Campanhas")
        status_2 = conversoes_total[conversoes_total['status'] == 2]
        st.markdown(f"**Menagens enviadas:** {len(status_2)}")
        status_4 = conversoes_total[conversoes_total['status'] == 4]
        st.markdown(f"**Conversões Atribuidas:** {len(status_4)}")
        st.markdown(f"**Taxa de conversão:** {len(status_4) / len(status_2) * 100:.2f}%")
        st.markdown(f"**Receita atribuida (status 4):** {formatar_moeda(status_4['totalamount'].sum())}")
        st.markdown(f"**Receita atribuida em porcentagem da receita total:** {status_4['totalamount'].sum() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown(f"**Receita por mensagem enviada:** {formatar_moeda(status_4['totalamount'].sum() / len(status_2))}")
        st.markdown("---")



    with st.expander("6 - Crescimento e Sazonalidade"):


        st.subheader("Índice 6.1 - CMGR — Compound Monthly Growth Rate")
        st.markdown(f"**Receita mai/2025:** {formatar_moeda(status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum())}")
        st.markdown(f"**Receita jan/2026:** {formatar_moeda(status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum())}")
        st.markdown(f"**Periodos compostos:** {9 - 1}")
        st.markdown(f"**CMGR:** {((status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum() / status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum()) ** (1/(9-1)) - 1) * 100:.2f}%")
        st.markdown(f"Equivalente anual: {(1 + ((status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum() / status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum()) ** (1/(9-1)) - 1))**12 - 1 :.2f}% a.a.")
        st.markdown("---")



        st.subheader("Índice 6.2 - Coeficiente de Variação Mensal da Receita")
        st.markdown(f"**Média mensal:** {formatar_moeda(status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().mean())}")
        st.markdown(f"**Desvio padrão mensal:** {formatar_moeda(status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().std())}")
        st.markdown(f"**CV mensal:** {status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().std() / status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().mean() * 100:.2f}%")
        st.markdown("---")



        st.subheader("Índice 6.3 - Concentração de Receita por Período do Dia")
        st.markdown(f"**Receita Noite porcentagem (18 - 23h):** {status_16[(status_16['createdat'].dt.hour >= 18) & (status_16['createdat'].dt.hour <= 23)]['totalamount'].sum() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown(f"**Pedidos Noite porcentagem (18 - 23h):** {len(status_16[(status_16['createdat'].dt.hour >= 18) & (status_16['createdat'].dt.hour <= 23)]) / len(status_16) * 100:.2f}%")
        st.markdown(f"**HHI por Periodo:** {status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().std() / status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().mean()}")
        st.markdown("---")



        st.subheader("Índice 6.4 - Variação Mensal da Receita")
        meses = [5, 6, 7, 8, 9, 10, 11, 12, 1]
        labels = ["mai -> jun", "jun -> jul", "jul -> ago", "ago -> set", "set -> out", "out -> nov", "nov -> dez", "dez -> jan"]
        for i in range(len(meses)-1):
            m1, m2 = meses[i], meses[i+1]
            rec1 = status_16[status_16['createdat'].dt.month == m1]['totalamount'].sum()
            rec2 = status_16[status_16['createdat'].dt.month == m2]['totalamount'].sum()
            var = ((rec2 - rec1) / rec1 * 100) if rec1 > 0 else 0
            st.markdown(f"**Variação mensal da receita ({labels[i]}):** {var:.2f}%")
        st.markdown("---")



    with st.expander("7 - Recorrência e Valor do Cliente"):


        st.subheader("Índice 7.1 - Taxa de Recorrência")
        clientes_pedidos = status_16.groupby('customerid').size()
        total_clientes_unicos = len(clientes_pedidos)
        clientes_recorrentes = len(clientes_pedidos[clientes_pedidos > 1])
        taxa_recorrencia = (clientes_recorrentes / total_clientes_unicos) * 100 if total_clientes_unicos > 0 else 0
        st.markdown(f"**Clientes c/ Pedido Concluído:** {total_clientes_unicos:,}".replace(",", "."))
        st.markdown(f"**Clientes Recorrentes:** {clientes_recorrentes:,}".replace(",", "."))
        st.markdown(f"**Taxa de Recorrência:** {taxa_recorrencia:.2f}%".replace(".", ","))
        st.markdown("---")



        st.subheader("Índice 7.2 - Participação dos Recorrentes na Receita")
        rec_recorrentes = status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum()
        rec_total_s16 = status_16['totalamount'].sum()
        st.markdown(f"**Receita dos recorrentes:** {formatar_moeda(rec_recorrentes)}")
        st.markdown(f"**Porcentagem da receita dos recorrentes:** {rec_recorrentes / rec_total_s16 * 100:.2f}%")
        rec_nao_recorrentes = status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum()
        st.markdown(f"**Receita dos não recorrentes:** {formatar_moeda(rec_nao_recorrentes)}")
        st.markdown(f"**Porcentagem da receita dos não recorrentes:** {rec_nao_recorrentes / rec_total_s16 * 100:.2f}%")
        st.markdown("---")



        st.subheader("Índice 7.3 - Frequência Média de Compra")
        st.markdown(f"**Pedidos / Cliente (todos):** {len(status_16) / total_clientes_unicos:.2f} pediso/cliente")
        st.markdown(f"**Pedidos / Cliente (recorrentes):** {len(status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]) / clientes_recorrentes:.2f} pedidos")
        st.markdown(f"**Pedidos / Cliente (unicos):** {len(status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]) / (total_clientes_unicos - clientes_recorrentes):.2f}")
        st.markdown("---")



        st.subheader("Índice 7.4 - ARPU Diferenciado")
        arpu_rec = status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / clientes_recorrentes
        arpu_nao_rec = status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / (total_clientes_unicos - clientes_recorrentes)
        st.markdown(f"**ARPU Recorrentes:** {arpu_rec:.2f}")
        st.markdown(f"**ARPU Não Recorrentes:** {arpu_nao_rec:.2f}")
        st.markdown(f"**Multiplicador:** {arpu_rec / arpu_nao_rec:.2f}")
        st.markdown("---")



    with st.expander("8 - Margem e Ponto de Equilíbrio"):


        st.subheader("Índice 8.1 - Margem de Contribuição Estimada")
        st.markdown(f"**Receita Total:** {formatar_moeda(rec_total_s16)}")
        
        cmv_percent = st.number_input("**CMV %:**" , min_value=0.0, max_value=100.0, value=32.0, step=0.1, key="cmv_percent")
        st.markdown(f"**(-) CMV :** {formatar_moeda(rec_total_s16 * (cmv_percent / 100))}")

        comissao_percent = st.number_input("**Comissão %:**" , min_value=0.0, max_value=100.0, value=18.0, step=0.1, key="comissao_percent")
        st.markdown(f"**(-) Comissão :** {formatar_moeda(rec_total_s16 * (comissao_percent / 100))}")

        op_variavel_percent = st.number_input("**Custos Variáveis %:**" , min_value=0.0, max_value=100.0, value=8.0, step=0.1, key="op_variavel_percent")
        st.markdown(f"**(-) Op. Variável :** {formatar_moeda(rec_total_s16 * (op_variavel_percent / 100))}")

        margem_contribuicao = rec_total_s16 - (rec_total_s16 * (cmv_percent / 100)) - (rec_total_s16 * (comissao_percent / 100)) - (rec_total_s16 * (op_variavel_percent / 100))
        st.markdown(f"**Margem de Contribuição:** {formatar_moeda(margem_contribuicao)}")
        margem_contribuicao_percent = margem_contribuicao / rec_total_s16 * 100
        st.markdown(f"**Margem de Contribuição %:** {margem_contribuicao_percent:.2f}%")
        st.markdown("---")



        st.subheader("Índice 8.3 - Ponto de Equilíbrio em Pedidos")
        mc_unitaria = status_16['totalamount'].mean() * (margem_contribuicao_percent / 100)
        st.markdown(f"**MC unitária por periodo:** {formatar_moeda(mc_unitaria)} / pedido")
        st.markdown(f"**Break-even RS 50k fixos:** {formatar_moeda(50000 / mc_unitaria)} pedidos / mês")
        st.markdown(f"**Break-even RS 100k fixos:** {formatar_moeda(100000 / mc_unitaria)} pedidos / mês")
        st.markdown(f"**Break-even RS 200k fixos:** {formatar_moeda(200000 / mc_unitaria)} pedidos / mês")
        st.markdown("---")



        st.subheader("Índice 8.4 - Margem Bruta de Canal (variando comissão)")
        receita_por_canal_m = status_16.groupby('saleschannel')['totalamount'].sum()
        margem_bruta_canal_p = (receita_por_canal_m / rec_total_s16) * 100
        canal_selecionado_m = st.selectbox("**Canal de venda:**", status_16['saleschannel'].unique(), key="canal_margem")
        st.markdown(formatar_moeda(receita_por_canal_m[canal_selecionado_m]))
        st.markdown(margem_bruta_canal_p[canal_selecionado_m])
        st.markdown(f"**{canal_selecionado_m} ({margem_bruta_canal_p[canal_selecionado_m]:.2f}%)**: {formatar_moeda(receita_por_canal_m[canal_selecionado_m] * (margem_bruta_canal_p[canal_selecionado_m]))}")
        st.markdown("---")
    

        

def page_campanhas():
    configurar_interface()
    campanhas_total, conversoes_total, pedidos_loja, mapa_lojas = carregar_dados()
    
    col_store_id = next((c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)
    if col_store_id:
        pedidos_loja['nome_loja'] = pedidos_loja[col_store_id].map(mapa_lojas).fillna("Desconhecida")
    else:
        pedidos_loja['nome_loja'] = "Desconhecida"

    lista_campanhas = sorted(campanhas_total['name'].unique())
    campanha_selecionada = st.selectbox("Selecione a Campanha para análise:", lista_campanhas)

    impactados, pedidos_convertidos, id_loja_campanha, nome_loja_atual, col_store_id_pedidos = processar_campanha(
        campanha_selecionada, campanhas_total, conversoes_total, pedidos_loja, mapa_lojas
    )

    taxa_conversao, receita_direta = renderizar_tab_campanhas_loja(
        impactados, pedidos_convertidos, id_loja_campanha, nome_loja_atual, 
        col_store_id_pedidos, campanhas_total, campanha_selecionada, pedidos_loja
    )

    st.sidebar.header("Visão Estratégica com IA")
    with st.sidebar.container():
        st.markdown("---")
        if st.button("Gerar Análise com IA"):
            with st.spinner('Analisando...'):
                resumo = {'impactados': len(impactados), 'conversao': taxa_conversao, 'receita_direta': receita_direta}
                st.markdown(f'<div class="ia-insight-box">💡 <b>Insight:</b><br>{obter_insight_ia(campanha_selecionada, resumo)}</div>', unsafe_allow_html=True)

def page_visao_geral():
    configurar_interface()
    _, _, pedidos_loja, mapa_lojas = carregar_dados()
    col_store_id = next((c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)
    if col_store_id:
        pedidos_loja['nome_loja'] = pedidos_loja[col_store_id].map(mapa_lojas).fillna("Desconhecida")
    else:
        pedidos_loja['nome_loja'] = "Desconhecida"
    
    renderizar_tab_visao_geral(pedidos_loja, col_store_id, mapa_lojas)

def page_testes():
    configurar_interface()
    _, conversoes_total, pedidos_loja, mapa_lojas = carregar_dados()
    col_store_id = next((c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)
    col_store_name = next((c for c in ['storename', 'STORENAME'] if c in pedidos_loja.columns), None)
    if col_store_id:
        pedidos_loja['nome_loja'] = pedidos_loja[col_store_id].map(mapa_lojas).fillna("Desconhecida")
    else:
        pedidos_loja['nome_loja'] = "Desconhecida"
    
    status_16 = pedidos_loja[pedidos_loja['status'] == 16]
    renderizar_tab_testes(pedidos_loja, status_16, col_store_id, col_store_name, mapa_lojas, conversoes_total)

    st.sidebar.image("Logo.svg")
    st.sidebar.header("Visão Financeira Contábil")
    with st.sidebar.container():
        st.markdown("Aqui estão todos os cálculos exigidos pelo professor para a entrega de contabilidade.")

if __name__ == "__main__":
    pg = st.navigation(
        [
            st.Page(page_campanhas, title="Campanhas", icon=":material/dashboard:", default=True),
            # st.Page(page_visao_geral, title="Visão Geral", icon=":material/public:"),
            st.Page(page_testes, title="Testes de Cálculos", icon=":material/analytics:"),
        ]
    )
    pg.run()
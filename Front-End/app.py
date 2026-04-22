import streamlit as st
import numpy as np
import pandas as pd
import os
import altair as alt
from openai import OpenAI


def configurar_interface():
    st.set_page_config(page_title="Análise de Performance", layout="wide")
    st.markdown("""
        <style>
        .stApp { 
            background-color: #FFE8E8; 
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

    df_campanhas['sendat'] = pd.to_datetime(
        df_campanhas['sendat'], errors='coerce', utc=True)
    df_pedidos_loja['createdat'] = pd.to_datetime(
        df_pedidos_loja['createdat'], errors='coerce', utc=True)

    return df_campanhas, df_conversoes, df_pedidos_loja, mapa_lojas


def processar_campanha(selecionada, campanhas_total, conversoes_total, pedidos_loja, mapa_lojas):
    dados_focados = campanhas_total[campanhas_total['name'] == selecionada]
    id_loja = dados_focados['storeid'].iloc[0] if 'storeid' in dados_focados.columns else None
    nome_loja = mapa_lojas.get(id_loja, f"Loja {id_loja}")
    clientes_imp = set(dados_focados['customerid'].dropna().unique())

    conv_vinculadas = conversoes_total[conversoes_total['customerid'].isin(
        clientes_imp)]
    if id_loja is not None and 'storeid' in conv_vinculadas.columns:
        conv_vinculadas = conv_vinculadas[conv_vinculadas['storeid'] == id_loja]

    col_order = next((c for c in ['order_id', 'orderid', 'ORDERID',
                     'id_pedido'] if c in conv_vinculadas.columns), None)
    col_store_pedidos = next(
        (c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)

    if col_order:
        pedidos_conv = pedidos_loja[pedidos_loja['id'].isin(
            conv_vinculadas[col_order])]
    else:
        pedidos_conv = pd.DataFrame()

    if id_loja is not None and col_store_pedidos:
        pedidos_conv = pedidos_conv[pedidos_conv[col_store_pedidos] == id_loja]

    return clientes_imp, pedidos_conv, id_loja, nome_loja, col_store_pedidos


def main():
    configurar_interface()
    campanhas_total, conversoes_total, pedidos_loja, mapa_lojas = carregar_dados()

    lista_campanhas = sorted(campanhas_total['name'].unique())
    campanha_selecionada = st.selectbox( "Selecione a Campanha para análise:", lista_campanhas)

    impactados, pedidos_convertidos, id_loja_campanha, nome_loja_atual, col_store_id_pedidos = processar_campanha(
        campanha_selecionada, campanhas_total, conversoes_total, pedidos_loja, mapa_lojas
    )

    tab1, tab2, tab3= st.tabs(["Campanhas (Por Loja)", "Visão Financeira (Por Loja)", "Visão Geral (Todas as Lojas)"])
    
    with tab1:

        clientes_convertidos = set(pedidos_convertidos['customerid'].unique(
        )) if not pedidos_convertidos.empty else set()
        taxa_conversao = (len(clientes_convertidos) / len(impactados)
                          * 100) if len(impactados) > 0 else 0
        receita_direta = pedidos_convertidos['totalamount'].sum(
        ) if not pedidos_convertidos.empty else 0

        data_lancamento = campanhas_total[campanhas_total['name']
                                          == campanha_selecionada]['sendat'].min()

        if not pd.isna(data_lancamento):
            janela_anterior = (pedidos_loja['createdat'] >= data_lancamento - pd.Timedelta(
                days=7)) & (pedidos_loja['createdat'] < data_lancamento)
            janela_posterior = (pedidos_loja['createdat'] >= data_lancamento) & (
                pedidos_loja['createdat'] <= data_lancamento + pd.Timedelta(days=7))

            if col_store_id_pedidos:
                rec_antes = pedidos_loja.loc[janela_anterior & (
                    pedidos_loja[col_store_id_pedidos] == id_loja_campanha), 'totalamount'].sum()
                rec_depois = pedidos_loja.loc[janela_posterior & (
                    pedidos_loja[col_store_id_pedidos] == id_loja_campanha), 'totalamount'].sum()
            else:
                rec_antes = pedidos_loja.loc[janela_anterior, 'totalamount'].sum(
                )
                rec_depois = pedidos_loja.loc[janela_posterior,
                                              'totalamount'].sum()

            variacao_loja = rec_depois - rec_antes
            porcentagem_variacao = (
                variacao_loja / rec_antes * 100) if rec_antes > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric("Clientes Impactados",
                        f"{len(impactados):,}".replace(",", "."))
            col2.metric("Clientes Convertidos",
                        f"{len(clientes_convertidos):,}".replace(",", "."))
            col3.metric("Taxa de Conversão",
                        f"{taxa_conversao:.2f}%".replace(".", ","))

            st.markdown("---")

            col4, col5, col6 = st.columns(3)
            col4.metric("Data de Lançamento",
                        data_lancamento.strftime('%d/%m/%Y'))
            col5.metric("Receita Direta Campanha",
                        formatar_moeda(receita_direta))
            col6.metric("Performance Total da Loja", f"{porcentagem_variacao:.2f}%".replace(
                ".", ","), delta=formatar_moeda(variacao_loja))

            st.subheader(f"Evolução Diária da Receita - {nome_loja_atual}")
            df_receita_diaria = pedidos_loja.copy()
            if col_store_id_pedidos:
                df_receita_diaria = df_receita_diaria[df_receita_diaria[col_store_id_pedidos]
                                                      == id_loja_campanha]

            df_receita_diaria['data'] = df_receita_diaria['createdat'].dt.date
            rec_agrupada = df_receita_diaria.groupby(
                'data')['totalamount'].sum().reset_index()
            rec_agrupada['data'] = pd.to_datetime(
                rec_agrupada['data']).dt.tz_localize('UTC')

            mask = (rec_agrupada['data'] >= data_lancamento - pd.Timedelta(days=7)
                    ) & (rec_agrupada['data'] <= data_lancamento + pd.Timedelta(days=7))
            dados_grafico = rec_agrupada.loc[mask].copy()
            dados_grafico['data_formatada'] = dados_grafico['data'].dt.strftime(
                '%d/%m')

            grafico = alt.Chart(dados_grafico).mark_bar(
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color="#491a13", offset=0), alt.GradientStop(
                        color='#913322', offset=1)],
                    x1=1, x2=1, y1=1, y2=0.3
                ),
                cornerRadius=25,
            ).encode(
                x=alt.X('data_formatada:N', title='Data', sort=None),
                y=alt.Y('totalamount:Q', title='Receita Total')
            ).properties(height=400)

            st.altair_chart(grafico, use_container_width=True)
        else:
            st.warning(
                "Data de lançamento não disponível para a campanha selecionada.")

    with tab2:
        def ticket_medio(pedidos_filtrados):
            if not pedidos_filtrados.empty:
                return pedidos_filtrados['totalamount'].mean()
            return 0

        st.subheader(f"Métricas Financeiras - {nome_loja_atual}")

        if col_store_id_pedidos:
            pedidos_da_loja = pedidos_loja[pedidos_loja[col_store_id_pedidos] == id_loja_campanha]
        else:
            pedidos_da_loja = pedidos_loja

        col7, col8 = st.columns(2)

        receita_geral_loja = pedidos_da_loja['totalamount'].sum()
        col7.metric("Receita Geral da Loja", formatar_moeda(receita_geral_loja))

        valor_ticket_medio = ticket_medio(pedidos_da_loja)
        col8.metric("Ticket Médio", formatar_moeda(valor_ticket_medio))

        st.markdown("---")

    with tab3:
        st.subheader("Visão Geral - Todas as Lojas")
        receita_total = pedidos_loja['totalamount'].sum()
        ticket_medio_geral = pedidos_loja['totalamount'].mean()
        col9, col10 = st.columns(2)
        col9.metric("Receita Total", formatar_moeda(receita_total))
        col10.metric("Ticket Médio Geral", formatar_moeda(ticket_medio_geral))

        pedidos_loja['nome_loja'] = pedidos_loja[col_store_id_pedidos].map(mapa_lojas) if col_store_id_pedidos else "Desconhecida"
        
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




    st.markdown("---")





    st.sidebar.header("Visão Estratégica com IA")
    with st.sidebar.container():
        st.markdown("---")

        if st.button("Gerar Análise com IA"):
            with st.spinner('Analisando...'):
                resumo = {'impactados': len(
                    impactados), 'conversao': taxa_conversao, 'receita_direta': receita_direta}
                st.markdown(
                    f'<div class="ia-insight-box">💡 <b>Insight:</b><br>{obter_insight_ia(campanha_selecionada, resumo)}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()

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

    mapa_lojas = dict(zip(df_stores['id'], df_stores['name']))

    for df, col in [(df_campanhas, 'sendat'), (df_pedidos_loja, 'createdat')]:
        df[col] = pd.to_datetime(df[col], errors='coerce', utc=True)
    df_pedidos_loja['scheduledat'] = pd.to_datetime(df_pedidos_loja['scheduledat'], format='mixed')

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

    tab1, tab2, tab3, tab4 = st.tabs(["Campanhas (Por Loja)", "Visão Financeira (Por Loja)", "Visão Geral (Todas as Lojas)", "Testes de cálculos"])
    
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
        # status_16 = pedidos_loja[pedidos_loja['status'] == 16]
        # receita_status_16 = status_16['subtotalamount'].sum()
        col9, col10, col11 = st.columns(3)
        col9.metric("Receita Total", formatar_moeda(receita_total))
        col10.metric("Ticket Médio Geral", formatar_moeda(ticket_medio_geral))
        # col11.metric("Pedidos com Status 16", formatar_moeda(receita_status_16))

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

    with tab4:
        st.subheader("Testes de Cálculos e Métricas")
        st.markdown("Aqui você pode realizar testes rápidos de cálculos ou métricas específicas relacionadas às campanhas ou lojas. Insira os valores desejados para obter resultados instantâneos.")

        st.title("1 - Estrutura da Receita")
        st.subheader("Indice 1.1 - Decomposição da Receita Reportada")
        status_16 = pedidos_loja[pedidos_loja['status'] == 16]
        receita_status_16 = status_16['subtotalamount'].sum()
        st.markdown(f"**Subtotal de Pedidos com Status 16:** {formatar_moeda(receita_status_16)}")
        st.markdown(f"**Total de descontos com Status 16:** {formatar_moeda(status_16['discountamount'].sum())}")
        st.markdown(f"**Total de taxas com Status 16:** {formatar_moeda(status_16['taxamount'].sum())}")
        st.markdown(f"**Receita total com Status 16:** {formatar_moeda(status_16['totalamount'].sum())}")
        st.markdown(f"**Porcentagem do total de receita**: {receita_status_16 / (status_16['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Porcentagem sobre as taxas com Status 16**: {status_16['taxamount'].sum() / (status_16['totalamount'].sum()) * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 1.2 - Receita Líquida Comercial")
        st.markdown(f"**Receita líquida comercial:** {formatar_moeda(receita_status_16 - (status_16['discountamount'].sum()))}")
        st.markdown(f"**Taxa de desconto sobre subtotal:** {status_16['discountamount'].sum() / status_16['subtotalamount'].sum() * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 1.3 - Taxa de Realização da Receita")
        st.markdown(f"**Receita potencial:** {len(pedidos_loja) * status_16['totalamount'].mean():,.2f}".replace(",", "."))
        st.markdown(f"**Receita realizada:** {formatar_moeda(status_16['totalamount'].sum())}")
        st.markdown(f"**Índice de realização:** {status_16['totalamount'].sum() / (len(pedidos_loja) * status_16['totalamount'].mean()) * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 1.4 - Custo de Oportunidade dos Não-Concluídos")
        st.markdown(f"**Pedidos não concluidos:** {len(pedidos_loja) - len(status_16)}")
        st.markdown(f"**Receita não realizada:** {formatar_moeda((len(pedidos_loja) - len(status_16)) * status_16['totalamount'].mean())}")
        st.markdown(f"**Porcentagem de receita não realizada:** {(len(pedidos_loja) - len(status_16)) * status_16['totalamount'].mean() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown("---")

        st.title("2 - Cancelamento e Qualidade")
        st.subheader("Índice 2.1 - Taxa de Cancelamento Efetivo")
        cancelados_8 = pedidos_loja[pedidos_loja['status'] == 8]
        cancelados_11 = pedidos_loja[pedidos_loja['status'] == 11]
        cancelados_14 = pedidos_loja[pedidos_loja['status'] == 14]
        cancelados = pd.concat([cancelados_8, cancelados_11, cancelados_14])
        st.markdown(f"**Pedidos cancelados:** {len(cancelados)}")
        st.markdown(f"**Taxa de cancelamento:** {len(cancelados) / len(pedidos_loja) * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 2.2 - Decomposição do Cancelamento por Origem")
        st.markdown(f"**Cancelados por estabelecimento:** {len(cancelados_8) / len(pedidos_loja) * 100:.2f}%")
        st.markdown(f"**Cancelados por cliente:** {len(cancelados_11) / len(pedidos_loja) * 100:.2f}%")
        st.markdown(f"**Expirados/timeout:** {len(cancelados_14) / len(pedidos_loja) * 100:.2f}%")
        st.markdown(f"**Soma das tres causas:** {len(cancelados) / len(pedidos_loja) * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 2.3 - Receita Perdida por Cancelamento Efetivo")
        st.markdown(f"**Receita perdida por cancelamento:** {formatar_moeda(cancelados['totalamount'].sum())}")
        st.markdown(f"**Receita perdida por cancelamento:** {formatar_moeda(len(cancelados) * status_16['totalamount'].mean())}")
        st.markdown(f"**Porcentagem de receita perdida por cancelamento:** {(len(cancelados) * status_16['totalamount'].mean()) / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown("---")

        st.title("3 - Eficiência e Produtividade")
        st.subheader("Índice 3.1 - Taxa de Ativação de Lojas")
        st.markdown(f"**Lojas cadastradadas:** {len(mapa_lojas)}")
        st.markdown(f"**Lojas ativas:** {pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0}")
        st.markdown(f"**Taxa de inativação:** {((pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0)) / len(mapa_lojas) * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 3.2 - Receita Média por Loja Ativa")
        st.markdown(f"**Receita por Loja Ativa:** {formatar_moeda(status_16['totalamount'].sum() / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0))}")
        st.markdown(f"**Receita Mensal Média/Loja:** {formatar_moeda(status_16['totalamount'].sum() / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0) / 9)}")
        st.markdown("---")

        st.subheader("Índice 3.3 - Receita Média Diária da Operação")
        periodo_dias = (pedidos_loja['scheduledat'].max() - pedidos_loja['scheduledat'].min()).days + 1
        st.markdown(f"**Periodo:** {periodo_dias}")
        st.markdown(f"**Receita Dia:** {formatar_moeda(status_16['totalamount'].sum() / periodo_dias)}")
        st.markdown(f"**Pedidos Dia:** {len(status_16) / periodo_dias:.2f}")
        st.markdown("---")

        st.subheader("Índice 3.4 - Volume Médio por Loja Ativa")
        st.markdown(f"**Pedidos por loja ativa:** {len(status_16) / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0):.2f}")
        st.markdown(f"**Pedidos/Loja/Mês:** {len(status_16) / (pedidos_loja[col_store_id_pedidos].nunique() if col_store_id_pedidos else 0) / 9:.2f}")
        st.markdown("---")

        st.subheader("Índice 3.5 - ARPU — Receita Média por Cliente")
        st.markdown(f"**Cliente com pedido com status 16:** {status_16['customerid'].nunique() if status_16['customerid'].nunique() > 0 else 0}")
        st.markdown(f"**ARPU:** {status_16['totalamount'].sum() / status_16['customerid'].nunique() if status_16['customerid'].nunique() > 0 else 0:.2f}")
        st.markdown("---")

        st.title("4 - Concentração e Risco")
        st.subheader("Índice 4.1 - HHI — Concentração por Canal de Venda") #Quase todos os resultados deram diferente, não entendo nada aqui nesse
        receita_total = pedidos_loja['subtotalamount'].sum()
        st.markdown(f"**Receita Total:** {formatar_moeda(receita_total)}")
        receita_por_canal = pedidos_loja.groupby('saleschannel')['subtotalamount'].sum()
        shares_receita = receita_por_canal / receita_total
        hhi_total_receita = (shares_receita**2).sum() * 10000
        canal_selecionado = st.selectbox("**Canal de venda:**", pedidos_loja['saleschannel'].unique())
        receita_canal_selecionado = pedidos_loja[pedidos_loja['saleschannel'] == canal_selecionado]['subtotalamount'].sum()
        share_receita_canal = (receita_canal_selecionado / receita_total) * 10000
        st.markdown(f"**Share ({canal_selecionado}):** {share_receita_canal:.2f}")
        share_receita_quadrado = (share_receita_canal / 10000)**2 * 10000
        st.markdown(f"**Share ao quadrado:** {share_receita_quadrado:.2f}") 
        st.markdown(f"**O maior share é**: {shares_receita.max() * 100:.2f}% do {receita_por_canal.idxmax()}") #Deu diferente
        st.markdown(f"**HHI Total do Mercado:** {hhi_total_receita:.2f}") #Deu diferente
        if hhi_total_receita > 5000:
            st.markdown("O mercado é um monopólio")
        elif hhi_total_receita > 2500:
            st.markdown("O mercado possui alta concentração")
        elif hhi_total_receita > 1500:
            st.markdown("O mercado está com concentração moderada")
        else:
            st.markdown("O mercado está desconcentrado")

        st.subheader("Índice 4.2 - HHI — Concentração por Loja")
        st.markdown(f"**Receita Total:** {formatar_moeda(receita_total)}")
        receita_por_loja = pedidos_loja.groupby('nome_loja')['subtotalamount'].sum()
        shares_receita_loja = receita_por_loja / receita_total
        hhi_total_receita_loja = (shares_receita_loja**2).sum() * 10000
        loja_selecionada = st.selectbox("**Loja:**", sorted(pedidos_loja['nome_loja'].unique()))
        receita_loja_selecionada = pedidos_loja[pedidos_loja['nome_loja'] == loja_selecionada]['subtotalamount'].sum()
        share_receita_loja = (receita_loja_selecionada / receita_total) * 10000
        st.markdown(f"**Share ({loja_selecionada}):** {share_receita_loja:.2f}")
        share_receita_loja_quadrado = (share_receita_loja / 10000)**2 * 10000
        st.markdown(f"**Share ao quadrado:** {share_receita_loja_quadrado:.2f}")
        maior_loja_nome = receita_por_loja.idxmax()
        st.markdown(f"**O maior share é**: {shares_receita_loja.max() * 100:.2f}% da loja {maior_loja_nome}") #Deu diferente
        st.markdown(f"**HHI Total do Mercado:** {hhi_total_receita_loja:.2f}") #Deu diferente
        if hhi_total_receita_loja > 5000:
            st.markdown("O mercado é um monopólio")
        elif hhi_total_receita_loja > 2500:
            st.markdown("O mercado possui alta concentração")
        elif hhi_total_receita_loja > 1500:
            st.markdown("O mercado está com concentração moderada")
        else:
            st.markdown("O mercado está desconcentrado")
        st.markdown("---")

        st.subheader("Índice 4.3 - Curva ABC de Receita por Loja")
        receita_por_loja = status_16.groupby('nome_loja')['subtotalamount'].sum().sort_values(ascending=False)
        receita_total_abc = receita_por_loja.sum()
        shares_abc = receita_por_loja / receita_total_abc
        top_1_val = shares_abc.iloc[0] * 100
        top_4_val = shares_abc.iloc[:4].sum() * 100
        top_10_val = shares_abc.iloc[:10].sum() * 100
        n_lojas_total = len(receita_por_loja)
        n_vinte_pct = round(n_lojas_total * 0.2)
        top_20_pct_val = shares_abc.iloc[:n_vinte_pct].sum() * 100
        st.markdown(f"**Top 1 Loja (Share):** {top_1_val:.2f}%")
        st.markdown(f"**Top 4 Lojas (Acumulado):** {top_4_val:.2f}%")
        st.markdown(f"**Top 10 Lojas (Acumulado):** {top_10_val:.2f}%")
        st.markdown(f"**Top 20% ({n_vinte_pct} Lojas):** {top_20_pct_val:.2f}%")
        st.markdown("---")

        st.subheader("Índice 4.4 - Coeficiente de Gini de Receita por Loja")
        st.markdown(f"**Gini de lojas:** {(shares_abc**2).sum():.2f}")
        if (shares_abc**2).sum() > 0.5:
            st.markdown("Muito alta desigualdade")
        elif (shares_abc**2).sum() > 0.25:
            st.markdown("Alta desigualdade")
        elif (shares_abc**2).sum() > 0.1:
            st.markdown("Desigualdade moderada")
        else:
            st.markdown("Desigualdade baixa")
        st.markdown("---")

        st.title("5 - Indicadores Promocionais")
        st.subheader("Índice 5.1 - Investimento Promocional como % da Receita")
        st.markdown(f"**Investimento promocional:** {formatar_moeda(status_16['discountamount'].sum())}")
        st.markdown(f"**Porcentagem sobre receita:** {status_16['discountamount'].sum() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown(f"**Porcentagem sobre subtotal:** {status_16['discountamount'].sum() / status_16['subtotalamount'].sum() * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 5.2 - Profundidade Média do Desconto")
        st.markdown(f"**Pedidos com desconto:** {len(status_16[status_16['discountamount'] > 0])}")
        st.markdown(f"**Porcentagem de pedidos com desconto:** {len(status_16[status_16['discountamount'] > 0]) / len(status_16) * 100:.2f}%")
        st.markdown(f"**Subtotal dos beneficiados:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['subtotalamount'].sum())}")
        st.markdown(f"**Profundidade Média:** {status_16['discountamount'].sum() / status_16[status_16['discountamount'] > 0]['subtotalamount'].sum() * 100:.2f}%")
        st.markdown(f"**Desconto absoluto médio:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean())}")
        st.markdown("---")

        st.subheader("Índice 5.3 - Análise de Uplift — Ticket com vs sem Desconto")
        st.markdown(f"**Ticket - pedidos com desconto:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['totalamount'].mean())}")
        st.markdown(f"**Ticket - pedidos sem desconto:** {formatar_moeda(status_16[status_16['discountamount'] == 0]['totalamount'].mean())}")
        st.markdown(f"**Uplift:** {(status_16[status_16['discountamount'] > 0]['totalamount'].mean() - status_16[status_16['discountamount'] == 0]['totalamount'].mean()) / status_16[status_16['discountamount'] == 0]['totalamount'].mean() * 100:.2f}%")
        st.markdown("---")
        
        st.subheader("Índice 5.4 - Custo Promocional por Pedido Beneficiado")
        st.markdown(f"**Custo / Pedido c/ Desconto:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean())}")
        st.markdown(f"**Custo / Pedido (geral):** {formatar_moeda(status_16['discountamount'].mean())}")
        st.markdown(f"**Custo promocional diluido:** {formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean() - status_16['discountamount'].mean())}")
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

        st.title("6 - Crescimento e Sazonalidade")
        st.subheader("Índice 6.1 - CMGR — Compound Monthly Growth Rate") #Não sei para que serve
        st.markdown(f"**Receita mai/2025:** {formatar_moeda(status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum())}")
        st.markdown(f"**Receita jan/2026:** {formatar_moeda(status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum())}")
        st.markdown(f"**Periodos compostos:** {9 - 1}") # Não sei de onde saiu esse 9
        st.markdown(f"**CMGR:** {((status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum() / status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum()) ** (1/(9-1)) - 1) * 100:.2f}%")
        st.markdown(f"Equivalente anual: {(1 + ((status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum() / status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum()) ** (1/(9-1)) - 1))**12 - 1 :.2f}% a.a.")#Deu MUITO diferente
        st.markdown("---")

        st.subheader("Índice 6.2 - Coeficiente de Variação Mensal da Receita") #Deu TUDO diferente
        st.markdown(f"**Média mensal:** {formatar_moeda(status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().mean())}")
        st.markdown(f"**Desvio padrão mensal:** {formatar_moeda(status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().std())}")
        st.markdown(f"**CV mensal:** {status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().std() / status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().mean() * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 6.3 - Concentração de Receita por Período do Dia")
        st.markdown(f"**Receita Noite porcentagem (18 - 23h):** {status_16[(status_16['createdat'].dt.hour >= 18) & (status_16['createdat'].dt.hour <= 23)]['totalamount'].sum() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown(f"**Pedidos Noite porcentagem (18 - 23h):** {len(status_16[(status_16['createdat'].dt.hour >= 18) & (status_16['createdat'].dt.hour <= 23)]) / len(status_16) * 100:.2f}%")
        st.markdown(f"**HHI por Periodo:** {status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().std() / status_16.groupby(status_16['createdat'].dt.month)['totalamount'].sum().mean()}") #NÃO ENTENDI ABSOLUTAMENTE NADA DESSE HHI POR PERIODO
        st.markdown("---")

        st.subheader("Índice 6.4 - Variação Mensal da Receita") #Deu TUDO diferente, mas pelo menos eu entendi
        st.markdown(f"**Variação mensal da receita (mai -> jun):** {((status_16[status_16['createdat'].dt.month == 6]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 5]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (jun -> jul):** {((status_16[status_16['createdat'].dt.month == 7]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 6]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 6]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (jul -> ago):** {((status_16[status_16['createdat'].dt.month == 8]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 7]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 7]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (ago -> set):** {((status_16[status_16['createdat'].dt.month == 9]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 8]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 8]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (set -> out):** {((status_16[status_16['createdat'].dt.month == 10]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 9]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 9]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (out -> nov):** {((status_16[status_16['createdat'].dt.month == 11]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 10]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 10]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (nov -> dez):** {((status_16[status_16['createdat'].dt.month == 12]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 11]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 11]['totalamount'].sum()) * 100:.2f}%")
        st.markdown(f"**Variação mensal da receita (dez -> jan):** {((status_16[status_16['createdat'].dt.month == 1]['totalamount'].sum() - status_16[status_16['createdat'].dt.month == 12]['totalamount'].sum()) / status_16[status_16['createdat'].dt.month == 12]['totalamount'].sum()) * 100:.2f}%")
        st.markdown("---")

        st.title("7 - Recorrência e Valor do Cliente")
        st.subheader("Índice 7.1 - Taxa de Recorrência")
        clientes_pedidos = status_16.groupby('customerid').size()
        total_clientes_unicos = len(clientes_pedidos)
        clientes_recorrentes = len(clientes_pedidos[clientes_pedidos > 1])
        taxa_recorrencia = (clientes_recorrentes / total_clientes_unicos) * 100
        st.markdown(f"**Clientes c/ Pedido Concluído:** {total_clientes_unicos:,}".replace(",", "."))
        st.markdown(f"**Clientes Recorrentes:** {clientes_recorrentes:,}".replace(",", "."))
        st.markdown(f"**Taxa de Recorrência:** {taxa_recorrencia:.2f}%".replace(".", ","))
        st.markdown("---")

        st.subheader("Índice 7.2 - Participação dos Recorrentes na Receita")
        st.markdown(f"**Receita dos recorrentes:** {formatar_moeda(status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum())}")
        st.markdown(f"**Porcentagem da receita dos recorrentes:** {status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown(f"**Receita dos não recorrentes:** {formatar_moeda(status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum())}")
        st.markdown(f"**Porcentagem da receita dos não recorrentes:** {status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / status_16['totalamount'].sum() * 100:.2f}%")
        st.markdown("---")

        st.subheader("Índice 7.3 - Frequência Média de Compra")
        st.markdown(f"**Pedidos / Cliente (todos):** {len(status_16) / total_clientes_unicos:.2f} pediso/cliente")
        st.markdown(f"**Pedidos / Cliente (recorrentes):** {len(status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]) / clientes_recorrentes:.2f} pedidos")
        st.markdown(f"**Pedidos / Cliente (unicos):** {len(status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]) / (total_clientes_unicos - clientes_recorrentes):.2f}")
        st.markdown("---")

        st.subheader("Índice 7.4 - ARPU Diferenciado")
        st.markdown(f"**ARPU Recorrentes:** {status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / clientes_recorrentes:.2f}")
        st.markdown(f"**ARPU Não Recorrentes:** {status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / (total_clientes_unicos - clientes_recorrentes):.2f}")
        st.markdown(f"**Multiplicador:** {(status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / clientes_recorrentes) / (status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum() / (total_clientes_unicos - clientes_recorrentes)):.2f}")
        st.markdown("---")

        st.title("8 - Margem e Ponto de Equilíbrio")
        st.subheader("Índice 8.1 - Margem de Contribuição Estimada")
        st.markdown(f"**Receita Total:** {formatar_moeda(status_16['totalamount'].sum())}")
        
        cmv_percent = st.number_input("**CMV %:**" , min_value=0.0, max_value=100.0, value=32.0, step=0.1, key="cmv_percent")
        st.markdown(f"**(-) CMV :** {formatar_moeda(status_16['totalamount'].sum() * (cmv_percent / 100))}")
    
        comissao_percent = st.number_input("**Comissão %:**" , min_value=0.0, max_value=100.0, value=18.0, step=0.1, key="comissao_percent")
        st.markdown(f"**(-) Comissão :** {formatar_moeda(status_16['totalamount'].sum() * (comissao_percent / 100))}")

        op_variavel_percent = st.number_input("**Custos Variáveis %:**" , min_value=0.0, max_value=100.0, value=8.0, step=0.1, key="op_variavel_percent")
        st.markdown(f"**(-) Op. Variável :** {formatar_moeda(status_16['totalamount'].sum() * (op_variavel_percent / 100))}")

        margem_contribuicao = status_16['totalamount'].sum() - (status_16['totalamount'].sum() * (cmv_percent / 100)) - (status_16['totalamount'].sum() * (comissao_percent / 100)) - (status_16['totalamount'].sum() * (op_variavel_percent / 100))
        st.markdown(f"**Margem de Contribuição:** {formatar_moeda(margem_contribuicao)}")
        margem_contribuicao_percent = margem_contribuicao / status_16['totalamount'].sum() * 100
        st.markdown(f"**Margem de Contribuição %:** {margem_contribuicao_percent:.2f}%")
        st.markdown("---")

        st.subheader("Índice 8.3 - Ponto de Equilíbrio em Pedidos")
        st.markdown(f"**MC unitária por periodo:** {formatar_moeda(status_16['totalamount'].mean() * (margem_contribuicao_percent / 100))} / pedido")
        st.markdown(f"**Break-even RS 50k fixos:** {formatar_moeda(50000 / (status_16['totalamount'].mean() * (margem_contribuicao_percent / 100)))} pedidos / mês")
        st.markdown(f"**Break-even RS 100k fixos:** {formatar_moeda(100000 / (status_16['totalamount'].mean() * (margem_contribuicao_percent / 100)))} pedidos / mês")
        st.markdown(f"**Break-even RS 200k fixos:** {formatar_moeda(200000 / (status_16['totalamount'].mean() * (margem_contribuicao_percent / 100)))} pedidos / mês")
        st.markdown("---")

        st.subheader("Índice 8.4 - Margem Bruta de Canal (variando comissão)")
        receita_por_canal = status_16.groupby('saleschannel')['totalamount'].sum()
        margem_bruta_canal = (receita_por_canal / status_16['totalamount'].sum()) * 100
        # margem_bruta_canal_percent = margem_bruta_canal / receita_por_canal * 100
        canal_selecionado = st.selectbox("**Canal de venda:**", status_16['saleschannel'].unique(), key="canal_margem")
        st.markdown(formatar_moeda(receita_por_canal[canal_selecionado]))
        st.markdown(margem_bruta_canal[canal_selecionado])
        st.markdown(f"**{canal_selecionado} ({margem_bruta_canal[canal_selecionado]:.2f}%)**: {formatar_moeda(receita_por_canal[canal_selecionado] * (margem_bruta_canal[canal_selecionado]))}")
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
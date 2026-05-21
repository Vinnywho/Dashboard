import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from streamlit_echarts import st_echarts, JsCode
from core.engine import formatar_moeda
from components.charts import (
    grafico_porcentagem, grafico_de_4_variaveis, 
    grafico_pizza, grafico_semi_circulo
)
from datetime import datetime
from scipy import stats
from sklearn.metrics import mean_squared_error, mean_absolute_error

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

def renderizar_tab_testes(pedidos_loja, status_16, col_store_id_pedidos, col_store_name, mapa_lojas, conversoes_total):
    st.subheader("Visão Financeira Contábil")
    st.markdown("Aqui estão todos os cálculos exigidos pelo professor para a entrega de contabilidade.")

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
        grafico_porcentagem("Taxa de Cancelamento", taxa_cancelamento)
        st.markdown("---")

        st.subheader("Índice 2.2 - Decomposição do Cancelamento por Origem")
        cancelados_por_estabeleceimento = f"{len(cancelados_8) / len(pedidos_loja) * 100:.2f}"
        cancelados_por_cliente = f"{len(cancelados_11) / len(pedidos_loja) * 100:.2f}"
        cancelados_por_timeout = f"{len(cancelados_14) / len(pedidos_loja) * 100:.2f}"
        soma_cancelados = f"{len(cancelados) / len(pedidos_loja) * 100:.2f}"
        dados_grafico2_2 = pd.DataFrame({
                'Categoria': ['Cancelados por estabelecimento', 'Cancelados por cliente', 'Expirados/timeout', 'Soma das tres causas'],
                'Valor': [cancelados_por_estabeleceimento, cancelados_por_cliente, cancelados_por_timeout, soma_cancelados]})
        grafico_de_4_variaveis(dados_grafico2_2)
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
                "top": 120, "left": 30, "right": 30, "cellSize": ["auto", 20],
                "range": str(ano_analise), "itemStyle": {"borderWidth": 0.5},
                "yearLabel": {"show": True},
                "dayLabel": {"nameMap": ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]},
                "monthLabel": {"nameMap": ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]}
            },
            "series": { "type": "heatmap", "coordinateSystem": "calendar", "data": data_heatmap }
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
        with col22: grafico_porcentagem("Porcentagem sobre receita", porcentagem_sobre_receita)
        with col23: grafico_porcentagem("Porcentagem sobre subtotal", porcentagem_sobre_subtotal)
        st.markdown("---")

        st.subheader("Índice 5.2 - Profundidade Média do Desconto")
        col24, col25, col26 = st.columns(3)
        col24.metric(f"Pedidos com desconto",f"{len(status_16[status_16['discountamount'] > 0])}")
        col25.metric(f"Subtotal dos beneficiados",f"{formatar_moeda(status_16[status_16['discountamount'] > 0]['subtotalamount'].sum())}")
        col26.metric(f"Desconto absoluto médio",f"{formatar_moeda(status_16[status_16['discountamount'] > 0]['discountamount'].mean())}")
        porcentagem_pedidos_com_desconto = f"{len(status_16[status_16['discountamount'] > 0]) / len(status_16) * 100:.2f}"
        profundidade_media = f"{status_16['discountamount'].sum() / status_16[status_16['discountamount'] > 0]['subtotalamount'].sum() * 100:.2f}"
        col27, col28 = st.columns(2)
        with col27: grafico_porcentagem("Porcentagem de pedidos com desconto", porcentagem_pedidos_com_desconto)
        with col28: grafico_porcentagem("Profundidade Média", profundidade_media)
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
        dados_grafico5_4 = pd.DataFrame({
                'Categoria': ['Custo / Pedido c/ Desconto', 'Custo / Pedido (geral)', 'Custo promocional diluido'],
                'Valor': [custo_pedido_desconto, custo_pedido_geral, custo_promocional_diluido]})
        grafico_pizza("Custo Promocional por Pedido Beneficiado (R$)",dados_grafico5_4)
        st.markdown("---")

        st.subheader("Índice 5.5 - Receita Atribuída a Campanhas")
        col29, col30 = st.columns(2)
        status_2 = conversoes_total[conversoes_total['status'] == 2]
        col29.metric("Menagens enviadas",f"{len(status_2)}")
        status_4 = conversoes_total[conversoes_total['status'] == 4]
        col29.metric("Conversões Atribuidas",f"{len(status_4)}")
        taxa_de_conversao = f"{len(status_4) / len(status_2) * 100:.2f}"
        receita_atribuida_porcentagem = f"{status_4['totalamount'].sum() / status_16['totalamount'].sum() * 100:.2f}"
        col29.metric("Receita atribuida (status 4)",f"{formatar_moeda(status_4['totalamount'].sum())}")
        col29.metric(f"Receita por mensagem enviada",f"{formatar_moeda(status_4['totalamount'].sum() / len(status_2))}")
        with col30:
            grafico_porcentagem("Taxa de conversão", taxa_de_conversao)
            grafico_porcentagem("Receita atribuida em porcentagem da receita total", receita_atribuida_porcentagem)
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
        clientes_pedidos = status_16.groupby('customerid').size()
        total_clientes_unicos = len(clientes_pedidos)
        clientes_recorrentes = len(clientes_pedidos[clientes_pedidos > 1])
        taxa_recorrencia = (clientes_recorrentes / total_clientes_unicos) * 100 if total_clientes_unicos > 0 else 0
        st.subheader("Índice 7.1 - Taxa de Recorrência")
        col_rec_1, col_rec_2 = st.columns([1, 2])
        with col_rec_1:
            st.metric("Clientes Únicos", f"{total_clientes_unicos:,}".replace(",", "."))
            st.metric("Clientes Recorrentes", f"{clientes_recorrentes:,}".replace(",", "."))
        with col_rec_2: grafico_porcentagem("Fidelização", f"{taxa_recorrencia:.2f}")
        st.markdown("---")

        st.subheader("Índice 7.2 - Participação dos Recorrentes na Receita")
        rec_recorrentes = status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]['totalamount'].sum()
        rec_total_s16 = status_16['totalamount'].sum()
        rec_nao_recorrentes = rec_total_s16 - rec_recorrentes
        pct_recorrentes = f"{(rec_recorrentes / rec_total_s16 * 100):.2f}"
        pct_nao_recorrentes = f"{(rec_nao_recorrentes / rec_total_s16 * 100):.2f}"
        col_rec_3, col_rec_4 = st.columns([1, 2])
        with col_rec_3:
            st.metric("Receita Recorrentes", formatar_moeda(rec_recorrentes))
            st.metric("Receita Não Recorrentes", formatar_moeda(rec_nao_recorrentes))
        with col_rec_4:
            df_rec_receita = pd.DataFrame({'Categoria': ['Não Recorrentes', 'Recorrentes'], 'Valor': [pct_nao_recorrentes, pct_recorrentes]})
            grafico_pizza("Share de Receita (%)", df_rec_receita)
        st.markdown("---")

        st.subheader("Índice 7.3 - Frequência Média de Compra")
        freq_geral = f"{len(status_16) / total_clientes_unicos:.2f}"
        pedidos_rec_only = f"{len(status_16[~status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]) / (total_clientes_unicos - clientes_recorrentes):.2f}"
        freq_rec = f"{len(status_16[status_16['customerid'].isin(clientes_pedidos[clientes_pedidos > 1].index)]) / clientes_recorrentes:.2f}"
        col_rec_5, col_rec_6, col_rec7_3 = st.columns(3)
        col_rec_5.metric("Pedidos / Cliente (Geral)", f"{freq_geral}")
        col_rec_6.metric("Pedidos / Cliente (Recorrentes)", f"{freq_rec}")
        col_rec7_3.metric("Pedidos / Cliente (Unicos)", f"{(pedidos_rec_only)}")
        st.markdown("---")

        st.subheader("Índice 7.4 - ARPU Diferenciado")
        arpu_rec = rec_recorrentes / clientes_recorrentes if clientes_recorrentes > 0 else 0
        rec_novos = rec_total_s16 - rec_recorrentes
        clientes_novos = total_clientes_unicos - clientes_recorrentes
        arpu_nao_rec = rec_novos / clientes_novos if clientes_novos > 0 else 0
        col_rec_7, col_rec_8 = st.columns([1, 2])
        with col_rec_7:
            st.metric("ARPU Recorrentes", formatar_moeda(arpu_rec))
            st.metric("ARPU Novos", formatar_moeda(arpu_nao_rec))
            st.metric("Multiplicador", f"{(arpu_rec / arpu_nao_rec if arpu_nao_rec > 0 else 0):.2f}x")
        with col_rec_8:
            df_arpu_comp = pd.DataFrame({'Categoria': ['Recorrente', 'Novo'], 'Valor': [f"{arpu_rec:.2f}", f"{arpu_nao_rec:.2f}"]})
            grafico_semi_circulo("Comparativo de Valor", df_arpu_comp)

    with st.expander("8 - Margem e Ponto de Equilíbrio"):
        st.subheader("Índice 8.1 - Margem de Contribuição Estimada")
        rec_total_s16 = status_16['totalamount'].sum()
        col_input_1, col_input_2, col_input_3 = st.columns(3)
        with col_input_1: cmv_percent = st.number_input("**CMV %:**" , min_value=0.0, max_value=100.0, value=32.0, step=0.1, key="cmv_percent_8")
        with col_input_2: comissao_percent = st.number_input("**Comissão %:**" , min_value=0.0, max_value=100.0, value=18.0, step=0.1, key="comissao_percent_8")
        with col_input_3: op_variavel_percent = st.number_input("**Custos Variáveis %:**" , min_value=0.0, max_value=100.0, value=8.0, step=0.1, key="op_variavel_percent_8")

        valor_cmv = rec_total_s16 * (cmv_percent / 100)
        valor_comissao = rec_total_s16 * (comissao_percent / 100)
        valor_custos_var = rec_total_s16 * (op_variavel_percent / 100)
        margem_contribuicao = rec_total_s16 - valor_cmv - valor_comissao - valor_custos_var
        margem_contribuicao_percent = (margem_contribuicao / rec_total_s16 * 100) if rec_total_s16 > 0 else 0
        col_graf_8_1, col_met_8_1 = st.columns([2, 1])
        with col_graf_8_1:
            df_margem = pd.DataFrame({'Categoria': ['CMV', 'Comissão', 'Custos Var.', 'Margem'], 'Valor': [valor_cmv, valor_comissao, valor_custos_var, margem_contribuicao]})
            grafico_de_4_variaveis(df_margem)
        with col_met_8_1:
            st.metric("Margem de Contribuição", formatar_moeda(margem_contribuicao))
            st.metric("Margem %", f"{margem_contribuicao_percent:.2f}%")
        st.markdown("---")

        st.subheader("Índice 8.3 - Ponto de Equilíbrio (Break-Even)")
        mc_unitaria = status_16['totalamount'].mean() * (margem_contribuicao_percent / 100)
        col_be_1, col_be_2, col_be_3 = st.columns(3)
        col_be_1.metric("MC Unitária Média", formatar_moeda(mc_unitaria))
        col_be_2.metric("Break-even (Fixos R$ 50k)", f"{int(50000 / mc_unitaria) if mc_unitaria > 0 else 0} ped")
        col_be_3.metric("Break-even (Fixos R$ 100k)", f"{int(100000 / mc_unitaria) if mc_unitaria > 0 else 0} ped")
        st.markdown("---")

        st.subheader("Índice 8.4 - Margem Bruta por Canal")
        canal_selecionado_m = st.selectbox("**Selecione o Canal para análise de margem:**", status_16['saleschannel'].unique(), key="canal_margem_8")
        comissao_canal = 1 - (st.number_input("**Comissão %:**" , min_value=0.0, max_value=100.0, value=23.0, step=0.1) / 100)
        receita_canal = status_16[status_16['saleschannel'] == canal_selecionado_m]['totalamount'].sum() * comissao_canal
        receita_canal_total = status_16[status_16['saleschannel'] == canal_selecionado_m]['totalamount'].sum()
        col_met_8_2, col_met_8_3 = st.columns(2)
        col_met_8_2.metric(f"Receita - {canal_selecionado_m}", formatar_moeda(receita_canal))
        col_met_8_2.metric("% Participação Total", f"{comissao_canal * 100:.2f}%")
        df_canal_margem = pd.DataFrame({'Categoria': [f'Restante ({canal_selecionado_m})', 'Margem Bruta Canal Est.'], 'Valor': [receita_canal_total, receita_canal]})
        with col_met_8_3: grafico_pizza(f"Distribuição Estimada - {canal_selecionado_m}", df_canal_margem)

def renderizar_tab_clientes(df_clientes, df_enderecos, pedidos_loja, filtro_classe):
    status_16 = pedidos_loja[pedidos_loja['status'] == 16].copy()
    
    agrupado = status_16.groupby('customerid').agg(
        total_gasto=('totalamount', 'sum'),
        total_pedidos=('id', 'count'),
        ultimo_pedido=('createdat', 'max'),
        ticket_medio=('totalamount', 'mean')
    ).reset_index()
    
    df_analise = df_clientes[['id', 'name', 'dateofbirth']].merge(
        agrupado, left_on='id', right_on='customerid', how='left'
    )
    
    data_maxima = status_16['createdat'].max()
    df_analise['dias_inatividade'] = (data_maxima - df_analise['ultimo_pedido']).dt.days
    
    def classificar(row):
        if pd.isna(row['total_pedidos']) or row['total_pedidos'] == 0: return "Sem Pedido"
        if row['dias_inatividade'] > 90: return "Em Risco"
        if row['total_pedidos'] >= 3: return "Recorrente"
        if row['total_pedidos'] == 2: return "Potencial"
        return "Ocasional"

    df_analise['classificacao'] = df_analise.apply(classificar, axis=1)
    df_filtrado = df_analise[df_analise['classificacao'].isin(filtro_classe)]
    
    st.subheader(f"Indicadores de Base ({len(df_filtrado):,} clientes)")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Gasto Total", f"R$ {df_filtrado['total_gasto'].sum():,.2f}")
    m2.metric("Ticket Médio", f"R$ {df_filtrado['ticket_medio'].mean():,.2f}")
    m3.metric("Pedidos Totais", f"{int(df_filtrado['total_pedidos'].sum()) if not df_filtrado.empty else 0}")

    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        dist = df_filtrado['classificacao'].value_counts().reset_index()
        dist.columns = ['Categoria', 'Valor']
        grafico_pizza("Composição da Base Filtrada", dist)
    with c2:
        df_filtrado['idade'] = df_filtrado['dateofbirth'].apply(lambda x: datetime.now().year - x.year if pd.notnull(x) else None)
        st.altair_chart(alt.Chart(df_filtrado.dropna(subset=['idade'])).mark_bar(color='#913322').encode(
            x=alt.X('idade:Q', bin=alt.Bin(maxbins=20), title='Idade'),
            y=alt.Y('count()', title='Qtd')
        ).properties(height=300), use_container_width=True)

    st.dataframe(df_filtrado[['name', 'id', 'classificacao', 'ultimo_pedido', 'total_pedidos', 'total_gasto', 'ticket_medio']], use_container_width=True, hide_index=True)
    st.markdown("---")
    st.subheader("Distribuição Geográfica")
    df_geo = df_enderecos['city'].value_counts().reset_index().head(10)
    col_c, col_info = st.columns([2, 1])
    
    with col_c:
        chart_city = alt.Chart(df_geo).mark_bar(color='#B04735', cornerRadiusEnd=15).encode(
            x=alt.X('count:Q', title='Quantidade de Clientes'),
            y=alt.Y('city:N', sort='-x', title='Cidade')
        ).properties(height=400)
        st.altair_chart(chart_city, use_container_width=True)
        
    with col_info:
        top_cidade = df_geo.iloc[0]['city'] if not df_geo.empty else "N/A"
        st.markdown(
            f"""
            <div style='display: flex; gap: 5px; flex-direction: column;'>
                <span style='color: #262730; font-size: 18px; font-weight: bold;'>
                    A maior concentração está em:
                </span>
                <span style='color: #64D248; font-size: 24px; font-weight: bold;'>
                    {top_cidade}
                </span>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
def renderizar_tab_inferencial(status_16, confianca):
    st.subheader(f"Regressão Linear (Nível de Confiança: {confianca*100:.0f}%)")
    
    df_reg = status_16[['subtotalamount', 'totalamount']].copy().dropna()
    
    if df_reg.empty:
        st.warning("Dados insuficientes para executar a análise de regressão.")
        return None

    x = df_reg['subtotalamount']
    y = df_reg['totalamount']
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    r_squared = r_value**2
    
    t_score = stats.t.ppf((1 + confianca) / 2, len(x) - 2)
    margem_erro = t_score * std_err
    
    previsoes_full = intercept + slope * x
    mse = mean_squared_error(y, previsoes_full)
    mae = mean_absolute_error(y, previsoes_full)
    
    st.markdown("### Métricas de Ajuste do Modelo")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("R² (Poder Explicativo)", f"{r_squared:.4f}")
    col2.metric("P-Value (Significância)", f"{p_value:.4f}")
    col3.metric("Erro Padrão", f"{std_err:.4f}")
    col4.metric("IC (Slope)", f"±{margem_erro:.4f}")
    
    st.markdown("---")
    st.markdown("### Gráfico de Dispersão e Linha de Tendência")
    
    amostra_grafico = df_reg.sample(n=min(5000, len(df_reg)), random_state=42)
    
    pontos = alt.Chart(amostra_grafico).mark_circle(color='#B04735', opacity=0.4).encode(
        x=alt.X('subtotalamount:Q', title='Subtotal (Valor Bruto em R$)'),
        y=alt.Y('totalamount:Q', title='Total Amount (Valor Líquido em R$)'),
        tooltip=['subtotalamount', 'totalamount']
    )
    
    x_min, x_max = x.min(), x.max()
    df_linha = pd.DataFrame({
        'subtotalamount': [x_min, x_max],
        'previsao': [intercept + slope * x_min, intercept + slope * x_max]
    })
    
    linha = alt.Chart(df_linha).mark_line(color='#913322', size=3).encode(
        x='subtotalamount:Q',
        y='previsao:Q'
    )
    
    st.altair_chart(pontos + linha, use_container_width=True)
    
    st.markdown("### Diagnóstico e Interpretação Direta")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"**Equação da Reta:** `Y = {intercept:.4f} + {slope:.4f} * X`")
        st.markdown(f"**Erro Médio Absoluto (MAE):** R$ {mae:.2f}")
        st.markdown(f"**Erro Quadrático Médio (MSE):** {mse:.2f}")
        
    with col_b:
        if r_squared > 0.7:
            st.success("**Alto poder explicativo:** A variação no valor bruto (Subtotal) explica muito bem o comportamento do valor líquido final.")
        else:
            st.warning("**Variabilidade não explicada:** Fatores adicionais fora o subtotal (como descontos ou taxas agressivas) estão impactando o valor final.")

        if p_value < 0.05:
            st.info(f"**Resultado Estatisticamente Relevante:** A cada R$ 1,00 de aumento no Subtotal, o Total Líquido varia em média **R$ {slope:.2f}**.")
        else:
            st.error("**Sem Relação Estatística Provada:** O subtotal não possui um impacto confiável sobre o valor total neste cenário.")

    prompt_estruturado = f"""
    Você é um assistente estatístico de alta precisão. Analise os resultados de uma Regressão Linear Simples executada sobre os dados operacionais e gere um insight executivo interpretativo curto, claro e direto.

    Diretrizes Estritas:
    1. Nunca arredonde os coeficientes estatísticos fornecidos (R², P-Valor, Slope, Intercepto, Erro Padrão). Use-os com a precisão exata fornecida.
    2. Explique o significado prático do R² em termos de variabilidade explicada.
    3. Avalie a significância estatística com base no P-Valor e no Nível de Confiança de {confianca*100:.0f}%.
    4. Apresente a interpretação econômica do Slope (o impacto de R$ 1,00 no subtotal em relação ao valor total).

    Dados Contábeis e Estatísticos do Modelo:
    - Variável Independente (X): Subtotalamount (Valor Bruto)
    - Variável Dependente (Y): Totalamount (Valor Líquido Comercial)
    - Tamanho da Amostra (N): {len(df_reg)}
    - R² (Coeficiente de Determinação): {r_squared:.6f}
    - P-Valor: {p_value:.6f}
    - Coeficiente Angular (Slope): {slope:.6f}
    - Intercepto (Beta 0): {intercept:.6f}
    - Erro Padrão do Estimador: {std_err:.6f}
    - Erro Médio Absoluto (MAE): {mae:.4f}
    - Erro Quadrático Médio (MSE): {mse:.4f}
    """

    return {
        'prompt': prompt_estruturado,
        'analise': 'Regressao Linear Simples'
    }
    
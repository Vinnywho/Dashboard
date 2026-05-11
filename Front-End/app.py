import streamlit as st
from core.styles import configurar_interface
from core.data_loader import carregar_dados
from core.engine import processar_campanha, obter_insight_ia
from components.tabs import renderizar_tab_campanhas_loja, renderizar_tab_testes
from core.auth import renderizar_tela_login

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
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        # from core.styles import configurar_interface
        # configurar_interface() 
        renderizar_tela_login()
    else:
        pg = st.navigation(
            [
                st.Page(page_campanhas, title="Campanhas", icon=":material/dashboard:", default=True),
                st.Page(page_testes, title="Testes de Cálculos", icon=":material/analytics:"),
            ]
        )
        if st.sidebar.button("Sair"):
            st.session_state["autenticado"] = False
            st.rerun()
            
        pg.run()
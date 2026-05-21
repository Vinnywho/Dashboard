import streamlit as st
import base64
import numpy as np
from datetime import datetime
from core.styles import configurar_interface
from core.data_loader import carregar_dados
from core.engine import processar_campanha, obter_insight_ia
from core.auth import renderizar_tela_login
from components.tabs import (
    renderizar_tab_campanhas_loja, 
    renderizar_tab_testes, 
    renderizar_tab_clientes, 
    renderizar_tab_inferencial
)

def gerar_html_pdf(df_auditoria):
    total_bruto = df_auditoria['subtotalamount'].sum()
    total_liquido = df_auditoria['totalamount'].sum()
    total_taxas = df_auditoria['taxamount'].sum()
    
    check = np.isclose(df_auditoria['totalamount'], 
                       df_auditoria['subtotalamount'] + df_auditoria['taxamount'] - df_auditoria['discountamount'])
    taxa_integridade = (check.sum() / len(check)) * 100 if len(check) > 0 else 0
    cor_status = "#28a745" if taxa_integridade == 100 else "#dc3545"

    html = f"""
    <div style="font-family:sans-serif; color:#333; padding:20px; border:1px solid #eee;">
        <h1 style="color:#913322; border-bottom:2px solid #913322;">Relatório de Auditoria Contábil</h1>
        <p style="font-size:12px; color:#666;">Sistema Cannolitsky | FECAP 2026</p>
        
        <div style="display:flex; justify-content:space-between; margin:20px 0;">
            <div style="background:#f4f4f4; padding:15px; border-radius:5px; width:30%;">
                <small>VALOR BRUTO</small><br><strong>R$ {total_bruto:,.2f}</strong>
            </div>
            <div style="background:#f4f4f4; padding:15px; border-radius:5px; width:30%;">
                <small>RECEITA LÍQUIDA</small><br><strong>R$ {total_liquido:,.2f}</strong>
            </div>
            <div style="background:{cor_status}; color:white; padding:15px; border-radius:5px; width:30%;">
                <small>INTEGRIDADE</small><br><strong>{taxa_integridade:.1f}%</strong>
            </div>
        </div>

        <h3>Amostragem de Dados</h3>
        <table style="width:100%; border-collapse:collapse; font-size:12px;">
            <thead>
                <tr style="background:#913322; color:white;">
                    <th style="padding:8px;">ID</th><th style="padding:8px;">Subtotal</th><th style="padding:8px;">Taxas</th><th style="padding:8px;">Total</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f"<tr><td style='border-bottom:1px solid #eee; padding:5px;'>{r.id}</td><td style='border-bottom:1px solid #eee; padding:5px;'>{r.subtotalamount:,.2f}</td><td style='border-bottom:1px solid #eee; padding:5px;'>{r.taxamount:,.2f}</td><td style='border-bottom:1px solid #eee; padding:5px;'>{r.totalamount:,.2f}</td></tr>" for _, r in df_auditoria.head(20).iterrows()])}
            </tbody>
        </table>
    </div>
    """
    return html
def page_campanhas():
    configurar_interface()
    campanhas_total, conversoes_total, pedidos_loja, mapa_lojas, _, _ = carregar_dados()
    
    with st.sidebar:
        st.header("Filtros de Campanha")
        lista_campanhas = sorted(campanhas_total['name'].unique())
        campanha_selecionada = st.selectbox("Escolha a Campanha:", lista_campanhas)
        st.markdown("---")
        st.subheader("Ações")
        gerar_ia = st.button("Gerar Insight com IA", use_container_width=True)

    impactados, pedidos_convertidos, id_loja_campanha, nome_loja_atual, col_store_id_pedidos = processar_campanha(
        campanha_selecionada, campanhas_total, conversoes_total, pedidos_loja, mapa_lojas
    )

    taxa_conversao, receita_direta = renderizar_tab_campanhas_loja(
        impactados, pedidos_convertidos, id_loja_campanha, nome_loja_atual, 
        col_store_id_pedidos, campanhas_total, campanha_selecionada, pedidos_loja
    )

    if gerar_ia:
        with st.sidebar:
            st.info("💡 " + obter_insight_ia(campanha_selecionada, {'impactados': len(impactados), 'conversao': taxa_conversao, 'receita_direta': receita_direta}))

def page_clientes():
    configurar_interface()
    _, _, pedidos_loja, _, df_clientes, df_enderecos = carregar_dados()
    
    with st.sidebar:
        st.header("Gestão de Base")
        filtro_classe = st.multiselect(
            "Filtrar Classificação:", 
            ["Recorrente", "Potencial", "Ocasional", "Em Risco", "Sem Pedido"],
            default=["Recorrente", "Potencial", "Ocasional", "Em Risco", "Sem Pedido"]
        )
    
    renderizar_tab_clientes(df_clientes, df_enderecos, pedidos_loja, filtro_classe)

def page_inferencial():
    configurar_interface()
    _, _, pedidos_loja, _, _, _ = carregar_dados()
    status_16 = pedidos_loja[pedidos_loja['status'] == 16]
    
    with st.sidebar:
        st.header("Configurações Estatísticas")
        confianca = st.select_slider("Nível de Confiança:", options=[0.90, 0.95, 0.99], value=0.95)
        st.markdown("---")
        st.subheader("Análise Avançada")
        gerar_ia = st.button("Interpretar Regressão com IA", use_container_width=True)
    
    dados_contexto = renderizar_tab_inferencial(status_16, confianca)

    if gerar_ia and dados_contexto:
        with st.sidebar:
            st.info("💡 " + obter_insight_ia(dados_contexto['prompt'], dados_contexto))

def page_testes():
    from core.styles import configurar_interface
    from core.data_loader import carregar_dados
    from components.tabs import renderizar_tab_testes

    configurar_interface()
    _, conversoes_total, pedidos_loja, mapa_lojas, _, _ = carregar_dados()
    
    col_store_id = next((c for c in ['storeid', 'STOREID'] if c in pedidos_loja.columns), None)
    col_store_name = next((c for c in ['storename', 'STORENAME'] if c in pedidos_loja.columns), None)
    
    if col_store_id:
        pedidos_loja['nome_loja'] = pedidos_loja[col_store_id].map(mapa_lojas).fillna("Desconhecida")
    else:
        pedidos_loja['nome_loja'] = "Desconhecida"

    status_16 = pedidos_loja[pedidos_loja['status'] == 16].copy()
    
    with st.sidebar:
        st.header("Painel de Auditoria")
        st.markdown("---")
        
        html_pdf = gerar_html_pdf(status_16)
        
        st.download_button(
            label="Exportar Relatório Profissional",
            data=html_pdf,
            file_name=f"auditoria_cannolitsky_{datetime.now().strftime('%Y%m%d')}.html",
            mime="text/html",
            use_container_width=True,
            help="O arquivo será baixado em HTML. Ao abrir no navegador, use Ctrl+P e 'Salvar como PDF' para manter a formatação profissional."
        )
    
    renderizar_tab_testes(pedidos_loja, status_16, col_store_id, col_store_name, mapa_lojas, conversoes_total)

if __name__ == "__main__":
    if "autenticado" not in st.session_state:
        st.session_state["autenticado"] = False

    if not st.session_state["autenticado"]:
        configurar_interface() 
        renderizar_tela_login()
    else:
        pg = st.navigation([
            st.Page(page_campanhas, title="Dashboard Geral", icon=":material/dashboard:", default=True),
            st.Page(page_clientes, title="Análise de Clientes", icon=":material/group:"),
            st.Page(page_inferencial, title="Modelagem Estatística", icon=":material/query_stats:"),
            st.Page(page_testes, title="Auditoria Contábil", icon=":material/analytics:"),
        ])
        
        with st.sidebar:
            st.markdown("---")
            if st.button("Encerrar Sessão", use_container_width=True):
                st.session_state["autenticado"] = False
                st.rerun()
        pg.run()
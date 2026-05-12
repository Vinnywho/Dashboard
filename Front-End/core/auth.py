import streamlit as st
from supabase import create_client, Client

def inicializar_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def autenticar_usuario(email, password):
    supabase = inicializar_supabase()
    try:
        response = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return response
    except Exception as e:
        return None

def cadastrar_usuario(email, password, nome_completo, cargo):
    supabase = inicializar_supabase()
    try:
        response = supabase.auth.sign_up({
            "email": email.strip(), 
            "password": password,
            "options": {
                "data": {
                    "full_name": nome_completo,
                    "role": cargo.lower()
                }
            }
        })
        return response
    except Exception as e:
        st.error(f"Erro técnico: {str(e)}")
        return None

def renderizar_tela_login():
    st.markdown("""
        <style>
        .auth-header {
            text-align: center;
            color: #913322;
            font-family: 'Montserrat', sans-serif;
            font-weight: 900;
            margin-bottom: 5px;
            letter-spacing: 1px;
        }
        .auth-subtitle {
            text-align: center;
            color: #565656;
            font-size: 0.9rem;
            margin-bottom: 30px;
        }
        /* Ajuste fino para os inputs dentro do card */
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    _, col_central, _ = st.columns([1, 1.5, 1])
    
    with col_central:
        st.write("")
        st.write("")
        
        with st.container(border=True):
            
            tab_login, tab_cadastro = st.tabs(["Acessar", "Novo Registro"])
            
            with tab_login:
                with st.form("form_login", clear_on_submit=False):
                    email = st.text_input("E-mail")
                    senha = st.text_input("Senha", type="password")
                    btn_entrar = st.form_submit_button("Entrar no Painel", use_container_width=True)
                    
                    if btn_entrar:
                        user = autenticar_usuario(email, senha)
                        if user:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_nome"] = email 
                            st.rerun()
                        else:
                            st.error("Credenciais inválidas")

            with tab_cadastro:
                with st.form("form_cadastro", clear_on_submit=False):
                    novo_nome = st.text_input("Nome Completo")
                    novo_email = st.text_input("E-mail")
                    nova_senha = st.text_input("Senha", type="password")
                    novo_cargo = st.selectbox("Cargo", ["Gestor", "Analista", "Admin"])
                    btn_criar = st.form_submit_button("Criar Conta", use_container_width=True)
                    
                    if btn_criar:
                        if novo_nome and novo_email and nova_senha:
                            res = cadastrar_usuario(novo_email, nova_senha, novo_nome, novo_cargo)
                            if res and hasattr(res, 'user') and res.user is not None:
                                st.success("Cadastro realizado com sucesso!")
                            elif res:
                                st.info("Cadastro pendente de validação.")
                        else:
                            st.warning("Preencha todos os campos obrigatórios.")
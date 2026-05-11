import streamlit as st

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
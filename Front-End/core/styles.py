import streamlit as st
import base64
import os

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return ""

def configurar_interface():
    st.set_page_config(page_title="Cannolitsky", layout="wide", page_icon="Logo.svg")
    
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    
    caminhos_possiveis = [
        os.path.join(diretorio_atual, "Logo_Branca.svg"),
        os.path.join(diretorio_atual, "..", "Logo_Branca.svg"),
        os.path.join(os.getcwd(), "Logo_Branca.svg"),
        os.path.join(os.getcwd(), "Front-End", "Logo_Branca.svg")
    ]
    
    logo_path = None
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            logo_path = caminho
            break
            
    img_base64 = get_base64_image(logo_path) if logo_path else ""

    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Anta&family=Bagel+Fat+One&family=Barrio&family=Bitcount:wght@100..900&family=Cabin:ital,wght@0,400..700;1,400..700&family=Cherry+Bomb+One&family=Coral+Pixels&family=Handjet:wght,ELSH@100..900,2&family=Honk:MORF@15&family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Josefin+Sans:ital,wght@0,100..700;1,100..700&family=Montserrat:ital,wght@0,100..900;1,100..900&family=Permanent+Marker&family=Poppins:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,100;1,200;1,300;1,400;1,500;1,600;1,700;1,800;1,900&family=Press+Start+2P&family=Rubik+Glitch&display=swap');

        .stApp {{ 
            background-color: #FCF8F8; 
        }}

        .main-header {{
            background: linear-gradient(90deg, #913322 0%, #B04735 100%);
            padding: 1.5rem 2.5rem;
            border-radius: 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2.5rem;
            box-shadow: 0 10px 30px rgba(145, 51, 34, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }}

        .header-content {{
            display: flex;
            align-items: center;
            gap: 20px;
        }}

        .headertitle {{
            color: #fff;
            font-family: 'Permanent Marker', sans-serif;
            font-weight: 100;
            font-size: 2.6rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 0;
            line-height: 1;
        }}

        .header-subtitle {{
            color: rgba(255, 255, 255, 0.8);
            font-family: 'Montserrat', sans-serif;
            font-size: 0.85rem;
            font-weight: 400;
            margin: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        [data-testid="stMetric"] {{
            background-color: white;
            border: 1px solid #eee;
            color: #31333F;
            padding: 20px;
            border-radius: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            transition: all 0.3s ease;
        }}

        [data-testid="stMetric"]:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(145, 51, 34, 0.1);
            border-color: #913322;
        }}

        [data-testid="stMetricValue"] {{
            font-size: 24px;
            font-weight: 900;
            color: #913322;
        }}

        [data-testid="stMetricLabel"] {{
            font-size: 14px;
            color: #565656;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .ia-insight-box {{
            background-color: white;
            border-left: 6px solid #913322;
            padding: 25px;
            border-radius: 1rem;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        }}
        </style>
    """, unsafe_allow_html=True)

    header_html = f"""
        <div class="main-header">
            <div class="header-content">
                <img src="data:image/svg+xml;base64,{img_base64}" width="60">
                <div>
                    <div class="headertitle">Cannolitsky</div>
                    <p class="header-subtitle">Performance & Inteligência Contábil</p>
                </div>
            </div>
        </div>
    """ if img_base64 else f"""
        <div class="main-header">
            <div class="header-content">
                <div>
                    <h1 class="header-title">Cannolitsky</h1>
                    <p class="header-subtitle">Performance & Inteligência Contábil</p>
                </div>
            </div>
        </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)
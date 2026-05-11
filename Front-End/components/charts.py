import streamlit as st
import altair as alt
from streamlit_echarts import st_echarts, JsCode

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
    return st_echarts(options=options, height="400px")

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
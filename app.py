import streamlit as st
import psychrolib
import numpy as np
import plotly.graph_objects as go

psychrolib.SetUnitSystem(psychrolib.SI)

st.set_page_config(
    page_title="Calculadora Psicrométrica v2.0",
    layout="wide"
)

st.title("🌬️ Calculadora Psicrométrica v2.0")

st.sidebar.header("Entradas")

Tdb = st.sidebar.number_input(
    "Temperatura de Bulbo Seco (°C)",
    value=25.0
)

RH = st.sidebar.slider(
    "Umidade Relativa (%)",
    0,
    100,
    60
) / 100

P = st.sidebar.number_input(
    "Pressão atmosférica (Pa)",
    value=101325
)

st.sidebar.markdown("---")

st.sidebar.header("Comparação (opcional)")

Tdb2 = st.sidebar.number_input(
    "Temperatura estado 2 (°C)",
    value=30.0
)

RH2 = st.sidebar.slider(
    "UR estado 2 (%)",
    0,
    100,
    50
) / 100

# =============================
# Cálculos psicrométricos
# =============================

W = psychrolib.GetHumRatioFromRelHum(Tdb, RH, P)
Tdp = psychrolib.GetTDewPointFromRelHum(Tdb, RH)
h = psychrolib.GetMoistAirEnthalpy(Tdb, W)
Twb = psychrolib.GetTWetBulbFromRelHum(Tdb, RH, P)

W2 = psychrolib.GetHumRatioFromRelHum(Tdb2, RH2, P)
h2 = psychrolib.GetMoistAirEnthalpy(Tdb2, W2)

# =============================
# RESULTADOS
# =============================

st.header("Resultados")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Razão de Umidade (kg/kg)", round(W, 5))
col2.metric("Ponto de Orvalho (°C)", round(Tdp, 2))
col3.metric("Bulbo Úmido (°C)", round(Twb, 2))
col4.metric("Entalpia (kJ/kg)", round(h/1000, 2))

# =============================
# COMPARAÇÃO
# =============================

st.header("Comparação entre Estados")

delta_h = (h2 - h)/1000

st.write("Diferença de entalpia:", round(delta_h,2),"kJ/kg")

# =============================
# GRÁFICO PSICROMÉTRICO
# =============================

st.header("Gráfico Psicrométrico")

T_range = np.linspace(0,50,100)

fig = go.Figure()

for rh in [0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]:

    W_line = [
        psychrolib.GetHumRatioFromRelHum(T, rh, P)
        for T in T_range
    ]

    fig.add_trace(go.Scatter(
        x=T_range,
        y=W_line,
        mode='lines',
        line=dict(width=1),
        name=f"{int(rh*100)}% UR"
    ))

fig.add_trace(go.Scatter(
    x=[Tdb],
    y=[W],
    mode="markers",
    marker=dict(size=12),
    name="Estado 1"
))

fig.add_trace(go.Scatter(
    x=[Tdb2],
    y=[W2],
    mode="markers",
    marker=dict(size=12),
    name="Estado 2"
))

fig.update_layout(
    xaxis_title="Temperatura de Bulbo Seco (°C)",
    yaxis_title="Razão de Umidade (kg/kg)",
    height=600
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

st.write("Ferramenta para ensino de Psicrometria aplicada à Engenharia Agrícola 🌱")
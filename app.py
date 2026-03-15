import streamlit as st
import psychrolib
import numpy as np
from psychro_chart import create_psychro_chart

psychrolib.SetUnitSystem(psychrolib.SI)

st.set_page_config(
    page_title="Psicrometria Pro",
    layout="wide"
)

st.title("🌬️ Psicrometria Pro")

st.sidebar.header("Condições do ar")

Tdb = st.sidebar.slider("Temperatura (°C)",0,50,30)

RH = st.sidebar.slider("Umidade Relativa (%)",0,100,60)/100

P = st.sidebar.number_input(
    "Pressão atmosférica (Pa)",
    value=101325
)

# ========================
# Cálculos
# ========================

W = psychrolib.GetHumRatioFromRelHum(Tdb,RH,P)

Twb = psychrolib.GetTWetBulbFromRelHum(Tdb,RH,P)

Tdp = psychrolib.GetTDewPointFromRelHum(Tdb,RH)

h = psychrolib.GetMoistAirEnthalpy(Tdb,W)

v = psychrolib.GetMoistAirVolume(Tdb,W,P)

# ========================
# RESULTADOS
# ========================

st.subheader("Propriedades do ar")

col1,col2,col3,col4,col5=st.columns(5)

col1.metric("Bulbo úmido",f"{Twb:.2f} °C")

col2.metric("Ponto de orvalho",f"{Tdp:.2f} °C")

col3.metric("Razão de mistura",f"{W:.5f} kg/kg")

col4.metric("Entalpia",f"{h/1000:.2f} kJ/kg")

col5.metric("Volume específico",f"{v:.3f} m³/kg")

# ========================
# Gráfico
# ========================

st.subheader("Carta psicrométrica")

fig=create_psychro_chart(P)

fig.add_scatter(
    x=[Tdb],
    y=[W],
    mode="markers",
    marker=dict(size=14),
    name="Estado do ar"
)

st.plotly_chart(fig,use_container_width=True)

import streamlit as st
import math
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Ambiência Wilhelm Pro", page_icon="🌡️", layout="wide")

# --- ESTILIZAÇÃO CSS CUSTOMIZADA ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { border: 1px solid #e0e0e0; padding: 15px; border-radius: 12px; background-color: white; }
    .status-container { padding: 20px; border-radius: 15px; margin-bottom: 25px; color: white; text-align: center; }
    .footer { text-align: center; color: #666; font-size: 0.8em; margin-top: 50px; border-top: 1px solid #ddd; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES MATEMÁTICAS (WILHELM, 1976) ---

def calcular_pws(t_c):
    T = t_c + 273.15
    if t_c < 0:
        return math.exp(24.2779 - (6238.64 / T) - 0.344438 * math.log(T))
    return math.exp((-7511.52 / T) + 89.63121 + (0.023998970 * T) - 
                    (1.1654551e-5 * (T**2)) - (1.2810336e-8 * (T**3)) + 
                    (2.0998405e-11 * (T**4)) - (12.150799 * math.log(T)))

def calcular_tdp_regressao(pw):
    a = math.log(pw)
    if pw <= 0.611: return 5.994 + 12.41 * a + 0.4273 * (a**2)
    elif pw <= 12.33: return 6.983 + 14.38 * a + 1.079 * (a**2)
    return 13.80 + 9.478 * a + 1.991 * (a**2)

def calcular_w_equacao_16(t, t_star, p):
    pws_star = calcular_pws(t_star)
    ws_star = 0.62198 * pws_star / (p - pws_star)
    num = (2501 - 2.411 * t_star) * ws_star - 1.006 * (t - t_star)
    den = 2501 + 1.775 * t - 4.186 * t_star
    return num / den

def encontrar_tbu_secante(t_bs, w_alvo, p, tdp_inicial):
    x0, x1 = tdp_inicial, t_bs
    def f(t_teste): return w_alvo - calcular_w_equacao_16(t_bs, t_teste, p)
    for _ in range(20):
        f_x0, f_x1 = f(x0), f(x1)
        if abs(f_x1 - f_x0) < 1e-9: break
        x2 = x1 - f_x1 * (x1 - x0) / (f_x1 - f_x0)
        x0, x1 = x1, x2
        if abs(x1 - x0) < 0.01: return x1
    return x1

# --- INTERFACE ---
st.title("📊 Calculadora de Ambiência Animal")
st.markdown("---")

# --- SIDEBAR ---
st.sidebar.header("🛠️ Configurações")
altitude = st.sidebar.number_input("Altitude (m)", value=918, step=1)
p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
st.sidebar.info(f"Pressão Atmosférica: {p_atm:.2f} kPa")
especie = st.sidebar.selectbox("Espécie Alvo", ["Bovino Leiteiro", "Aves", "Suínos"])

# --- ÁREA DE ENTRADA ---
with st.container():
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        metodo = st.selectbox("Método de Entrada", ["TBS e UR%", "TBS e TBU", "TBS e TPO"])
        tbs = st.number_input("Temp. Bulbo Seco (°C)", value=28.0, step=0.1)
    with col_input2:
        if metodo == "TBS e UR%":
            dado2 = st.slider("Umidade Relativa (%)", 0.0, 100.0, 60.0)
        elif metodo == "TBS e TBU":
            dado2 = st.number_input("Temp. Bulbo Úmido (°C)", value=21.0, step=0.1)
        else:
            dado2 = st.number_input("Temp. Ponto de Orvalho (°C)", value=18.0, step=0.1)

# --- CÁLCULOS ---
if st.button("CALCULAR PROPRIEDADES", use_container_width=True):
    try:
        # Lógica de cálculo conforme Wilhelm (1976)
        if metodo == "TBS e UR%":
            phi = dado2 / 100.0
            pws = calcular_pws(tbs)
            pw = phi * pws
            w = 0.62198 * pw / (p_atm - pw)
            tdp = calcular_tdp_regressao(pw)
            tbu = encontrar_tbu_secante(tbs, w, p_atm, tdp)
        elif metodo == "TBS e TBU":
            tbu = dado2
            w = calcular_w_equacao_16(tbs, tbu, p_atm)
            pw = (p_atm * w) / (0.62198 + w)
            phi = (pw / calcular_pws(tbs)) * 100
            tdp = calcular_tdp_regressao(pw)
        else:
            tdp = dado2
            pw = calcular_pws(tdp)
            phi = (pw / calcular_pws(tbs)) * 100
            w = 0.62198 * pw / (p_atm - pw)
            tbu = encontrar_tbu_secante(tbs, w, p_atm, tdp)

        itu = (tbs + 273.15) + 0.36 * (tdp + 273.15) - 330.08
        h = 1.006 * tbs + w * (2501 + 1.775 * tbs)

        # Lógica de Status (Cores)
        if especie == "Bovino Leiteiro":
            limit_c, limit_a = 72, 79
        else:
            limit_c, limit_a = 74, 79
            
        if itu < limit_c: color, status = "#2e7d32", "CONFORTO"
        elif itu < limit_a: color, status = "#f9a825", "ALERTA"
        else: color, status = "#c62828", "PERIGO"

        # --- EXIBIÇÃO ---
        st.markdown(f"<div class='status-container' style='background-color: {color};'><h2>ITU: {itu:.2f} — {status}</h2></div>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🌡️ Bulbo Úmido", f"{tbu:.2f} °C")
        m2.metric("💧 Umidade Relativa", f"{phi if metodo != 'TBS e UR%' else dado2:.1f} %")
        m3.metric("🔥 Entalpia (h)", f"{h:.2f} kJ/kg")
        m4.metric("🌫️ Ponto Orvalho", f"{tdp:.2f} °C")

        # --- GRÁFICO PSICROMÉTRICO DINÂMICO ---
        st.subheader("📍 Ponto de Estado no Diagrama Psicrométrico")
        
        # Gerar curvas de UR constante para o fundo do gráfico
        t_range = np.linspace(0, 45, 100)
        fig = go.Figure()
        
        for p_rel in [20, 40, 60, 80, 100]:
            w_line = [0.62198 * (p_rel/100 * calcular_pws(ti)) / (p_atm - (p_rel/100 * calcular_pws(ti))) for ti in t_range]
            fig.add_trace(go.Scatter(x=t_range, y=w_line, mode='lines', line=dict(width=1, color='rgba(100,100,100,0.3)'), name=f"UR {p_rel}%", showlegend=False))

        # Adicionar o ponto atual
        fig.add_trace(go.Scatter(x=[tbs], y=[w], mode='markers+text', marker=dict(color='red', size=12), text=["PONTO ATUAL"], textposition="top center", name="Estado do Ar"))

        fig.update_layout(xaxis_title="Temperatura Bulbo Seco (°C)", yaxis_title="Razão de Mistura (kg/kg)", height=450, template="simple_white")
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erro no processamento: {e}")

st.markdown(f"<div class='footer'>Baseado em Wilhelm (1976) | Desenvolvido por Alexandre Klein - UFLA</div>", unsafe_allow_html=True)

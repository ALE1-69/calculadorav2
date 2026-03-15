import streamlit as st
import math
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Ambiência Wilhelm Pro", page_icon="🌡️", layout="wide")

# --- ESTILIZAÇÃO CSS (CORREÇÃO DE CORES) ---
st.markdown("""
    <style>
    /* Força cor escura em textos globais e inputs */
    html, body, [class*="st-"] {
        color: #1c1e21;
    }
    .stMetric {
        border: 1px solid #d1d5db;
        padding: 15px;
        border-radius: 12px;
        background-color: #ffffff !important;
    }
    /* Garante que o texto da métrica seja legível */
    [data-testid="stMetricValue"] {
        color: #0288d1 !important;
    }
    [data-testid="stMetricLabel"] {
        color: #374151 !important;
    }
    .status-container {
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        color: white !important;
        text-align: center;
        font-weight: bold;
    }
    .footer {
        text-align: center;
        color: #6b7280;
        font-size: 0.85em;
        margin-top: 50px;
        padding: 20px;
        border-top: 1px solid #e5e7eb;
    }
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
st.title("🌡️ Ambiência Animal - Wilhelm (1976)")
st.caption(f"**Alexandre Klein** | Engenharia Agrícola - UFLA")
st.markdown("---")

# --- SIDEBAR ---
st.sidebar.header("🛠️ Configurações")
altitude = st.sidebar.number_input("Altitude (m)", value=918, step=1)
p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
st.sidebar.info(f"Pressão Atmosférica: {p_atm:.2f} kPa")
especie = st.sidebar.selectbox("Espécie Alvo", ["Bovino Leiteiro", "Aves", "Suínos"])

# --- ÁREA DE ENTRADA ---
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

        itu = tbs + 0.36 * tdp + 41.404 # Simplificação da fórmula do usuário
        h = 1.006 * tbs + w * (2501 + 1.775 * tbs)

        limit_c = 72 if especie == "Bovino Leiteiro" else 74
        limit_a = 79
            
        if itu < limit_c: color, status = "#2e7d32", "CONFORTO"
        elif itu < limit_a: color, status = "#f9a825", "ALERTA"
        else: color, status = "#c62828", "PERIGO"

        st.markdown(f"<div class='status-container' style='background-color: {color};'><h2>ITU: {itu:.2f} — {status}</h2></div>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🌡️ Bulbo Úmido", f"{tbu:.2f} °C")
        m2.metric("💧 Umid. Relativa", f"{phi if metodo != 'TBS e UR%' else dado2:.1f} %")
        m3.metric("🔥 Entalpia (h)", f"{h:.2f} kJ/kg")
        m4.metric("🌫️ Ponto Orvalho", f"{tdp:.2f} °C")

        # --- GRÁFICO PSICROMÉTRICO COM ZONA DE CONFORTO ---
        st.subheader("📍 Análise Gráfica e Zona de Conforto")
        t_range = np.linspace(10, 45, 100)
        fig = go.Figure()

        # 1. Curva de Saturação (UR 100%)
        w_sat = [0.62198 * calcular_pws(ti) / (p_atm - calcular_pws(ti)) for ti in t_range]
        fig.add_trace(go.Scatter(x=t_range, y=w_sat, mode='lines', line=dict(color='black', width=2), name="Saturação"))

        # 2. Sombreamento da Zona de Conforto (ITU < limit_c)
        # Tdp = (ITU - Tbs - 41.404) / 0.36
        w_conforto = []
        t_conforto = np.linspace(10, limit_c - 41.404, 50) # Tbs não pode ser maior que o limite
        for ti in t_conforto:
            tdp_limit = (limit_c - ti - 41.404) / 0.36
            if tdp_limit > ti: tdp_limit = ti # Tdp não pode ser > Tbs
            pw_limit = calcular_pws(tdp_limit)
            w_limit = 0.62198 * pw_limit / (p_atm - pw_limit)
            w_conforto.append(w_limit)

        fig.add_trace(go.Scatter(
            x=list(t_conforto) + [t_conforto[0]], 
            y=list(w_conforto) + [0], 
            fill='toself', fillcolor='rgba(46, 125, 50, 0.2)', 
            line=dict(color='rgba(255,255,255,0)'), name="Zona de Conforto"
        ))

        # 3. Ponto Atual
        fig.add_trace(go.Scatter(x=[tbs], y=[w], mode='markers', marker=dict(color='red', size=15, symbol='x'), name="Estado Atual"))

        fig.update_layout(
            xaxis=dict(title="Temperatura Bulbo Seco (°C)", range=[10, 45]),
            yaxis=dict(title="Razão de Mistura (kg/kg)", range=[0, 0.035]),
            height=500, margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Verifique os dados. TBU/TPO não podem ser maiores que a TBS.")

st.markdown(f"<div class='footer'>Baseado em Wilhelm (1976) | Desenvolvido para a disciplina de Construções e Ambiência - UFLA</div>", unsafe_allow_html=True)

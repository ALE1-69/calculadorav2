import streamlit as st
import math
import plotly.graph_objects as go
import numpy as np

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Ambiência Wilhelm Pro", page_icon="🌡️", layout="wide")

# --- CSS PARA FORÇAR TEMA CLARO E LEGÍVEL ---
st.markdown("""
    <style>
    /* Força o fundo da página como branco */
    .stApp {
        background-color: #FFFFFF;
    }
    /* Força todos os textos principais para cinza escuro/preto */
    h1, h2, h3, p, span, label {
        color: #1F2937 !important;
    }
    /* Estilização das métricas (caixas de resultado) */
    [data-testid="stMetric"] {
        background-color: #F9FAFB !important;
        border: 1px solid #E5E7EB !important;
        padding: 15px !important;
        border-radius: 10px !important;
    }
    [data-testid="stMetricValue"] {
        color: #0288d1 !important;
    }
    /* Ajuste das caixas de entrada (Inputs) */
    .stTextInput>div>div>input, .stNumberInput>div>div>input {
        color: #1F2937 !important;
        background-color: #FFFFFF !important;
    }
    /* Container de Status (ITU) */
    .status-box {
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
        border: 1px solid rgba(0,0,0,0.1);
    }
    .status-text {
        color: #FFFFFF !important; /* Texto do ITU sempre branco para contrastar com a cor do box */
        font-weight: bold;
        margin: 0;
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

# --- CONTEÚDO PRINCIPAL ---
st.title("🌡️ Ambiência Animal - Wilhelm (1976)")
st.markdown(f"**Alexandre Klein** | Engenharia Agrícola - UFLA")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("⚙️ Configurações")
altitude = st.sidebar.number_input("Altitude (m)", value=918)
p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
st.sidebar.info(f"Pressão: {p_atm:.2f} kPa")
especie = st.sidebar.selectbox("Espécie", ["Bovino Leiteiro", "Aves", "Suínos"])

# --- ENTRADAS ---
c_in1, c_in2 = st.columns(2)
with c_in1:
    metodo = st.selectbox("Método de Entrada", ["TBS e UR%", "TBS e TBU", "TBS e TPO"])
    tbs = st.number_input("Temp. Bulbo Seco (°C)", value=28.0)
with c_in2:
    if metodo == "TBS e UR%":
        dado2 = st.slider("Umidade Relativa (%)", 0.0, 100.0, 60.0)
    elif metodo == "TBS e TBU":
        dado2 = st.number_input("Temp. Bulbo Úmido (°C)", value=21.0)
    else:
        dado2 = st.number_input("Temp. Ponto de Orvalho (°C)", value=18.0)

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

        itu = tbs + 0.36 * tdp + 41.404
        h = 1.006 * tbs + w * (2501 + 1.775 * tbs)

        limit_c = 72 if especie == "Bovino Leiteiro" else 74
        color = "#2e7d32" if itu < limit_c else "#f9a825" if itu < 79 else "#c62828"
        status = "CONFORTO" if itu < limit_c else "ALERTA" if itu < 79 else "PERIGO"

        # Box de Status
        st.markdown(f"""
            <div class='status-box' style='background-color: {color};'>
                <h2 class='status-text'>ITU: {itu:.2f} — {status}</h2>
            </div>
        """, unsafe_allow_html=True)

        # Métricas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🌡️ Bulbo Úmido", f"{tbu:.2f} °C")
        m2.metric("💧 Umid. Relativa", f"{phi if metodo != 'TBS e UR%' else dado2:.1f}%")
        m3.metric("🔥 Entalpia (h)", f"{h:.2f} kJ/kg")
        m4.metric("🌫️ Ponto Orvalho", f"{tdp:.2f} °C")

        # --- GRÁFICO ---
        st.subheader("📍 Análise de Conforto Térmico")
        t_range = np.linspace(10, 45, 100)
        fig = go.Figure()

        # Curva de Saturação
        w_sat = [0.62198 * calcular_pws(ti) / (p_atm - calcular_pws(ti)) for ti in t_range]
        fig.add_trace(go.Scatter(x=t_range, y=w_sat, mode='lines', line=dict(color='#1F2937', width=2), name="Saturação"))

        # Zona de Conforto Sombreada
        t_conf = np.linspace(10, limit_c - 41.404, 50)
        w_conf = []
        for ti in t_conf:
            tdp_l = (limit_c - ti - 41.404) / 0.36
            if tdp_l > ti: tdp_l = ti
            w_conf.append(0.62198 * calcular_pws(tdp_l) / (p_atm - calcular_pws(tdp_l)))

        fig.add_trace(go.Scatter(x=list(t_conf) + [t_conf[0]], y=list(w_conf) + [0], 
                                 fill='toself', fillcolor='rgba(46, 125, 50, 0.2)', 
                                 line=dict(color='rgba(255,255,255,0)'), name="Zona de Conforto"))

        # Ponto Atual
        fig.add_trace(go.Scatter(x=[tbs], y=[w], mode='markers', marker=dict(color='#EF4444', size=15, symbol='x'), name="Estado Atual"))

        fig.update_layout(template="simple_white", xaxis_title="Bulbo Seco (°C)", yaxis_title="W (kg/kg)", height=500)
        st.plotly_chart(fig, use_container_width=True)

    except Exception:
        st.error("Erro nos dados. Verifique os valores inseridos.")

st.markdown("<div style='text-align: center; color: #9CA3AF; padding: 20px;'>GEA117 - Engenharia Agrícola - UFLA</div>", unsafe_allow_html=True)
st.markdown(f"<div class='footer'>Baseado em Wilhelm (1976) | Desenvolvido para a disciplina de Construções e Ambiência - UFLA</div>", unsafe_allow_html=True)

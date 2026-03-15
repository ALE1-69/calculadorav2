import streamlit as st
import math

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Ambiência Wilhelm Pro",
    page_icon="🌡️",
    layout="wide"
)

# --- CSS PARA ESTILIZAÇÃO ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .result-card {
        background-color: #e1f5fe;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #0288d1;
        margin-bottom: 20px;
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
        if abs(x1 - x0) < 0.001: return x1
    return x1

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 4])
with col_titulo:
    st.title("🌡️ Calculadora de Ambiência Animal")
    st.caption("Universidade Federal de Lavras | Eng. Agrícola | GEA117")

# --- ABAS ---
tab_calc, tab_info = st.tabs(["🚀 Calculadora", "📚 Sobre o Modelo"])

with tab_calc:
    # --- CONFIGURAÇÕES NA SIDEBAR ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2921/2921944.png", width=100)
    st.sidebar.title("Configurações Técnicas")
    altitude = st.sidebar.number_input("Altitude Local (m)", value=918, help="Padrão Lavras: 918m")
    p_atm = 101.325 * (1 - 2.25577e-5 * altitude)**5.25588
    st.sidebar.info(f"Pressão Atmosférica: **{p_atm:.2f} kPa**")
    
    st.sidebar.divider()
    especie = st.sidebar.selectbox("Espécie Alvo", ["Bovino Leiteiro", "Aves", "Suínos"])

    # --- INPUTS PRINCIPAIS ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Entradas Térmicas")
        metodo = st.selectbox("Método de Entrada", ["TBS e UR%", "TBS e TBU", "TBS e TPO"])
        tbs = st.number_input("Temp. Bulbo Seco (°C)", value=28.0, step=0.1)
    
    with c2:
        st.subheader("Variável Secundária")
        if metodo == "TBS e UR%":
            dado2 = st.slider("Umidade Relativa (%)", 0.0, 100.0, 55.0)
        elif metodo == "TBS e TBU":
            dado2 = st.number_input("Temp. Bulbo Úmido (°C)", value=20.0, step=0.1)
        else:
            dado2 = st.number_input("Temp. Ponto de Orvalho (°C)", value=15.0, step=0.1)

    st.divider()

    # --- CÁLCULOS E RESULTADOS ---
    if st.button("🚀 PROCESSAR DADOS PSICROMÉTRICOS", use_container_width=True):
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

            h = 1.006 * tbs + w * (2501 + 1.775 * tbs)
            v = 0.28705 * (tbs + 273.15) * (1 + 1.6078 * w) / p_atm
            itu = (tbs + 273.15) + 0.36 * (tdp + 273.15) - 330.08

            # Lógica de Status
            if especie == "Bovino Leiteiro":
                if itu < 72: color, status = "#2e7d32", "CONFORTO"
                elif itu < 79: color, status = "#f9a825", "ALERTA (ESTRESSE LEVE)"
                else: color, status = "#c62828", "PERIGO (ESTRESSE GRAVE)"
            else:
                if itu < 74: color, status = "#2e7d32", "CONFORTO"
                elif itu < 79: color, status = "#f9a825", "ALERTA"
                else: color, status = "#c62828", "PERIGO"

            # --- EXIBIÇÃO DOS RESULTADOS ---
            st.markdown(f"""
                <div class='result-card' style='border-left-color: {color};'>
                    <h2 style='color: {color}; margin: 0;'>ITU: {itu:.2f} — {status}</h2>
                    <p style='color: #555;'>Espécie selecionada: {especie}</p>
                </div>
            """, unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🌡️ T. Bulbo Úmido", f"{tbu:.2f} °C")
            m2.metric("💧 Umidade Relativa", f"{phi if metodo != 'TBS e UR%' else dado2:.1f} %")
            m3.metric("🔥 Entalpia (h)", f"{h:.2f} kJ/kg")
            m4.metric("🌫️ Ponto de Orvalho", f"{tdp:.2f} °C")

            with st.expander("📝 Ver Detalhes Adicionais"):
                st.write(f"**Volume Específico:** {v:.4f} m³/kg")
                st.write(f"**Razão de Mistura (W):** {w:.5f} kg/kg")
                st.write(f"**Pressão de Vapor (Pw):** {pw:.4f} kPa")

        except Exception as e:
            st.error("Erro nos cálculos. Verifique se os valores são fisicamente possíveis para a altitude informada.")

with tab_info:
    st.subheader("Fundamentação Teórica")
    st.write("""
    Esta calculadora utiliza as equações de **Wilhelm (1976)**, publicadas na ASAE, que definem as propriedades psicrométricas 
    em unidades do Sistema Internacional (SI). 
    
    A grande vantagem deste modelo é a precisão nas equações de regressão para pressão de saturação e a utilização de um nível 
    de referência de 0 °C para o cálculo da entalpia.
    """)
    st.info("Referência: Wilhelm, L. R. (1976). Numerical Calculation of Psychrometric Properties in SI Units. ASAE.")

st.plotly_chart(fig,use_container_width=True)

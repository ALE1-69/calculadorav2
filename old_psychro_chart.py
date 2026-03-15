import numpy as np
import plotly.graph_objects as go
import psychrolib

psychrolib.SetUnitSystem(psychrolib.SI)

def create_psychro_chart(P):

    T = np.linspace(0,50,200)

    fig = go.Figure()

    # =========================
    # Linhas de umidade relativa
    # =========================

    for rh in np.arange(0.1,1.1,0.1):

        W = [psychrolib.GetHumRatioFromRelHum(t,rh,P) for t in T]

        fig.add_trace(go.Scatter(
            x=T,
            y=W,
            mode="lines",
            line=dict(width=1),
            name=f"{int(rh*100)}% UR",
            opacity=0.5
        ))

    # =========================
    # Linhas de entalpia
    # =========================

    for h in range(10,120,10):

        T_line=[]
        W_line=[]

        for t in T:

            W = (h*1000 - 1.006*t)/(2501 + 1.86*t)

            if W>0 and W<0.03:

                T_line.append(t)
                W_line.append(W)

        fig.add_trace(go.Scatter(
            x=T_line,
            y=W_line,
            mode="lines",
            line=dict(dash="dot"),
            name=f"h={h} kJ/kg",
            opacity=0.4
        ))

    # =========================
    # Linhas de volume específico
    # =========================

    for v in np.arange(0.75,0.95,0.05):

        T_line=[]
        W_line=[]

        for t in T:

            W=((v*P)/(287*(t+273)) -1)/1.6078

            if W>0 and W<0.03:

                T_line.append(t)
                W_line.append(W)

        fig.add_trace(go.Scatter(
            x=T_line,
            y=W_line,
            mode="lines",
            line=dict(dash="dash"),
            name=f"v={round(v,2)}",
            opacity=0.4
        ))

    fig.update_layout(

        title="Gráfico Psicrométrico",

        xaxis_title="Temperatura de Bulbo Seco (°C)",

        yaxis_title="Razão de Umidade (kg/kg)",

        height=700,

        legend=dict(font=dict(size=10))
    )

    return fig

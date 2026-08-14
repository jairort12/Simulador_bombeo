import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import fluids
from CoolProp.CoolProp import PropsSI
import pandas as pd
import io
import math
st.set_page_config(page_title="Simulador de Bombeo Avanzado", layout="wide")


# --- INICIO DEL BLOQUE DE SEGURIDAD ---
def verificar_contrasena():
    def contrasena_ingresada():
        if st.session_state["contrasena"] == st.secrets["password_cliente"]:
            st.session_state["contrasena_correcta"] = True
            del st.session_state["contrasena"]
        else:
            st.session_state["contrasena_correcta"] = False

    if "contrasena_correcta" not in st.session_state:
        st.text_input("🔑 Ingrese la contraseña de acceso:", type="password", on_change=contrasena_ingresada, key="contrasena")
        return False
    elif not st.session_state["contrasena_correcta"]:
        st.text_input("🔑 Ingrese la contraseña de acceso:", type="password", on_change=contrasena_ingresada, key="contrasena")
        st.error("🚫 Contraseña incorrecta.")
        return False
    else:
        return True

if not verificar_contrasena():
    st.stop()
# --- FIN DEL BLOQUE DE SEGURIDAD ---

st.title("⚙️ Simulador de Bomba de Engranajes y Pérdidas de Carga")

# ==========================================
# 1. BARRA LATERAL (INPUTS DEL SISTEMA)
# ==========================================
st.sidebar.header("Parámetros de la Bomba")
cilindrada_cm3 = st.sidebar.number_input("Cilindrada (cm³/rev)", value=15.0)
rpm = st.sidebar.slider("Revoluciones del Motor (RPM)", 500, 3000, 1450, 50)
presion_bypass_bar = st.sidebar.number_input("Tarado Válvula de Alivio (bar)", value=5.0)
coef_slip = st.sidebar.number_input("Coeficiente de Slip (Cs)", value=1.2e-12, format="%e")

st.sidebar.header("Parámetros de Tubería y Fluido")
diametro_mm = st.sidebar.slider("Diámetro interno tubería (mm)", 3.0, 25.0, 9.5) # 3/8 pulgada aprox
longitud_m = st.sidebar.number_input("Longitud total (m)", value=7.0)
k_valvulas = st.sidebar.number_input("Suma de K (Solenoide + Orificio 1/8)", value=50.0)
viscosidad_cp = st.sidebar.number_input("Viscosidad (cP)", value=1.0) # Similar al agua
densidad = 1000 # kg/m3

# Conversiones a SI
Vd = cilindrada_cm3 * 1e-6 # m3/rev
D = diametro_mm / 1000.0 # m
Area = math.pi * (D**2) / 4.0
mu = viscosidad_cp / 1000.0 # Pa.s
presion_bypass_pa = presion_bypass_bar * 1e5

# ==========================================
# 2. SECCIÓN ACADÉMICA (LATEX)
# ==========================================
with st.expander("📖 Ver Ecuaciones del Modelo Matemático"):
    st.write("El sistema evalúa el punto de convergencia donde la presión requerida por la red iguala el caudal real de la bomba tras sufrir pérdidas volumétricas por deslizamiento (slip).")
    
    st.subheader("Curva Resistente del Sistema")
    st.latex(r"\Delta P_{sys} = \left( f \frac{L}{D} + \sum K \right) \frac{\rho v^2}{2}")
    
    st.subheader("Caudal de la Bomba de Engranajes")
    st.latex(r"Q_{teo} = V_d \times \frac{N}{60}")
    st.latex(r"Q_{slip} = C_s \frac{\Delta P_{sys}}{\mu}")
    st.latex(r"Q_{real} = Q_{teo} - Q_{slip}")

# ==========================================
# 3. ALGORITMO ITERATIVO (SOLVER)
# ==========================================
st.header("Análisis Transitorio (Válvula Abierta)")

Q_teo = Vd * (rpm / 60.0) # m3/s
Q_real = Q_teo # Valor inicial asumido

tolerancia = 1e-7
error = 1.0
iteraciones = 0
max_iter = 100

# Bucle While para encontrar la convergencia
while error > tolerancia and iteraciones < max_iter:
    # 1. Calcular velocidad en la tubería
    v = Q_real / Area
    
    # 2. Calcular fricción (Asumimos turbulento simplificado o factor constante para el ejemplo)
    # En un modelo real robusto, aquí usarías fluids.friction.friction_factor
    f = 0.025 
    
    # 3. Calcular caída de presión del sistema (Pa)
    P_sys = (f * (longitud_m / D) + k_valvulas) * (densidad * v**2) / 2.0
    
    # 4. Calcular Slip
    Q_slip = coef_slip * (P_sys / mu)
    
    # 5. Nuevo caudal real (evitando caudales negativos si el slip es masivo)
    Q_nuevo = max(0.0, Q_teo - Q_slip)
    
    # 6. Evaluar error y actualizar
    error = abs(Q_nuevo - Q_real)
    Q_real = Q_nuevo
    iteraciones += 1

# ==========================================
# 4. RESULTADOS Y ALERTAS
# ==========================================
Q_real_lpm = Q_real * 60000.0
Q_teo_lpm = Q_teo * 60000.0
P_sys_bar = P_sys / 1e5

col1, col2, col3 = st.columns(3)
col1.metric("Caudal Teórico (L/min)", f"{Q_teo_lpm:.2f}")
col2.metric("Caudal Real Final (L/min)", f"{Q_real_lpm:.2f}", delta=f"-{(Q_teo_lpm - Q_real_lpm):.2f} Slip", delta_color="inverse")
col3.metric("Contrapresión del Sistema", f"{P_sys_bar:.2f} bar")

# Lógica de la Válvula Bypass
st.write("---")
if P_sys_bar > presion_bypass_bar:
    st.error(f"🚨 **¡ALERTA DE BYPASS!** La contrapresión ({P_sys_bar:.2f} bar) supera el tarado de la válvula de alivio ({presion_bypass_bar} bar). El fluido recirculará y el caudal a la salida caerá a cero.")
else:
    st.success("✅ El sistema opera por debajo de la presión de alivio.")

# ==========================================
# 5. GRÁFICA DE CONVERGENCIA
# ==========================================
st.subheader("Punto de Operación del Sistema")

# Generar curvas para graficar
caudales_plot = np.linspace(0, Q_teo * 1.2, 50)
p_sistema_plot = (f * (longitud_m / D) + k_valvulas) * (densidad * (caudales_plot/Area)**2) / 2.0 / 1e5

# Curva teórica de la bomba (Slip)
p_bomba_plot = np.linspace(0, presion_bypass_bar * 1.5, 50)
q_bomba_plot = np.maximum(0, Q_teo - (coef_slip * (p_bomba_plot * 1e5) / mu))

fig = go.Figure()
# Curva del Sistema
fig.add_trace(go.Scatter(x=caudales_plot*60000, y=p_sistema_plot, mode='lines', name='Curva del Sistema (Resistencia)', line=dict(color='red', width=3)))
# Curva de la Bomba
fig.add_trace(go.Scatter(x=q_bomba_plot*60000, y=p_bomba_plot, mode='lines', name='Curva de Bomba (con Slip)', line=dict(color='blue', width=3)))
# Punto de operación
fig.add_trace(go.Scatter(x=[Q_real_lpm], y=[P_sys_bar], mode='markers', name='Punto de Operación', marker=dict(color='green', size=12, symbol='star')))
# Límite Bypass
fig.add_hline(y=presion_bypass_bar, line_dash="dash", line_color="orange", annotation_text="Límite Válvula de Alivio")

fig.update_layout(xaxis_title="Caudal (L/min)", yaxis_title="Presión (bar)", template="plotly_white")
st.plotly_chart(fig, use_container_width=True)
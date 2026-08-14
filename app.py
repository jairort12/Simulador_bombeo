import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import fluids
from CoolProp.CoolProp import PropsSI

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

st.title("🚰 Simulador de Bombeo - Motor Plotly")

# 1. Barra lateral
st.sidebar.header("Parámetros del Sistema")
altura_fija = st.sidebar.slider("Diferencia de altura actual (m)", min_value=1.0, max_value=50.0, value=10.0, step=1.0)
eficiencia = st.sidebar.slider("Eficiencia de la bomba (%)", min_value=10, max_value=100, value=75, step=5)
temp_agua = st.sidebar.slider("Temperatura del agua (°C)", min_value=5.0, max_value=90.0, value=25.0, step=1.0)

# 2. Cálculos físicos base
densidad = PropsSI('D', 'T', temp_agua + 273.15, 'P', 101325, 'Water')
gravedad = 9.81
eficiencia_decimal = eficiencia / 100.0

col1, col2 = st.columns(2)
col1.metric("Densidad del agua", f"{densidad:.2f} kg/m³")

# 3. Gráfico 2D Interactivo (Potencia vs Caudal para la altura fija)
caudales_Lps = np.linspace(0.1, 10, 50)
potencia_2d_kw = ((densidad * gravedad * altura_fija * (caudales_Lps / 1000)) / eficiencia_decimal) / 1000

col2.metric("Potencia requerida a 5 L/s", f"{np.interp(5, caudales_Lps, potencia_2d_kw):.2f} kW")

st.subheader("Curva de Rendimiento 2D")
fig2d = px.line(x=caudales_Lps, y=potencia_2d_kw, 
                labels={'x': 'Caudal (L/s)', 'y': 'Potencia (kW)'},
                title=f"Potencia vs Caudal (Altura: {altura_fija} m)")
fig2d.update_traces(line=dict(color="#1f77b4", width=3))
st.plotly_chart(fig2d, use_container_width=True)

# 4. Gráfico 3D de Superficie (Potencia evaluando múltiples alturas y caudales)
st.subheader("Exploración 3D del Sistema")

alturas_array = np.linspace(1, 50, 50)
# Crear una malla (grid) para cruzar todas las alturas con todos los caudales
Q_mesh, H_mesh = np.meshgrid(caudales_Lps, alturas_array)

# Calcular la potencia para cada punto de la malla
P_mesh_kw = ((densidad * gravedad * H_mesh * (Q_mesh / 1000)) / eficiencia_decimal) / 1000

fig3d = go.Figure(data=[go.Surface(z=P_mesh_kw, x=caudales_Lps, y=alturas_array, colorscale='Viridis')])
fig3d.update_layout(
    title='Potencia Requerida vs Caudal y Altura',
    scene=dict(
        xaxis_title='Caudal (L/s)',
        yaxis_title='Altura (m)',
        zaxis_title='Potencia (kW)'
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)
st.plotly_chart(fig3d, use_container_width=True)
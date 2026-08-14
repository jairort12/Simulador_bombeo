import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import fluids
from CoolProp.CoolProp import PropsSI

st.set_page_config(page_title="Simulador de Bombeo Básico", layout="wide")

# --- INICIO DEL BLOQUE DE SEGURIDAD ---
def verificar_contrasena():
    """Devuelve True si el usuario ingresó la contraseña correcta."""
    
    def contrasena_ingresada():
        """Comprueba si la contraseña es correcta."""
        if st.session_state["contrasena"] == st.secrets["password_cliente"]:
            st.session_state["contrasena_correcta"] = True
            del st.session_state["contrasena"]  # Borra la contraseña por seguridad
        else:
            st.session_state["contrasena_correcta"] = False

    if "contrasena_correcta" not in st.session_state:
        # Primera vez: Muestra la caja de texto
        st.text_input("🔑 Ingrese la contraseña de acceso:", type="password", on_change=contrasena_ingresada, key="contrasena")
        return False
    elif not st.session_state["contrasena_correcta"]:
        # Contraseña incorrecta
        st.text_input("🔑 Ingrese la contraseña de acceso:", type="password", on_change=contrasena_ingresada, key="contrasena")
        st.error("🚫 Contraseña incorrecta.")
        return False
    else:
        # Contraseña correcta
        return True

# Detiene la ejecución si la contraseña no es correcta
if not verificar_contrasena():
    st.stop()
# --- FIN DEL BLOQUE DE SEGURIDAD ---

st.title("🚰 Simulador de Bombeo - Prueba de Concepto")
st.write("Cálculo de potencia requerida usando Bernoulli y propiedades de CoolProp.")

# 2. Barra lateral (Sidebar) para los inputs del usuario
st.sidebar.header("Parámetros del Sistema")
altura = st.sidebar.slider("Diferencia de altura (m)", min_value=1.0, max_value=50.0, value=10.0, step=1.0)
eficiencia = st.sidebar.slider("Eficiencia de la bomba (%)", min_value=10, max_value=100, value=75, step=5)
temp_agua = st.sidebar.slider("Temperatura del agua (°C)", min_value=5.0, max_value=90.0, value=25.0, step=1.0)

# 3. Cálculos físicos
# Obtener densidad del agua a presión atmosférica usando CoolProp
densidad = PropsSI('D', 'T', temp_agua + 273.15, 'P', 101325, 'Water')
gravedad = 9.81
eficiencia_decimal = eficiencia / 100.0

# Rango de caudales para la gráfica (0 a 10 L/s convertido a m3/s)
caudales_Lps = np.linspace(0.1, 10, 50)
caudales_m3s = caudales_Lps / 1000

# Ecuación de potencia: P = (densidad * g * H * Q) / eficiencia
potencia_watts = (densidad * gravedad * altura * caudales_m3s) / eficiencia_decimal
potencia_kw = potencia_watts / 1000

# 4. Mostrar resultados numéricos
col1, col2 = st.columns(2)
col1.metric("Densidad del agua (CoolProp)", f"{densidad:.2f} kg/m³")
col2.metric("Potencia requerida a 5 L/s", f"{np.interp(5, caudales_Lps, potencia_kw):.2f} kW")

# 5. Generar y mostrar la gráfica
st.subheader("Curva de Potencia vs Caudal")
fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(caudales_Lps, potencia_kw, color='#1f77b4', linewidth=2, label=f'Altura: {altura} m')
ax.set_xlabel("Caudal (L/s)")
ax.set_ylabel("Potencia (kW)")
ax.set_title("Potencia requerida vs Caudal")
ax.grid(True, linestyle='--', alpha=0.7)
ax.legend()

st.pyplot(fig)
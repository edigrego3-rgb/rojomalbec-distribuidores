import streamlit as st
import pandas as pd
import os
import sys

# --- RUTAS ---
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from modules.data_manager import load_catalog_data
from modules.utils import redondear_precio, extraer_descripcion, generar_mensaje_whatsapp

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Rojo Malbec B2B | Distribuidores",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO PREMIUM DARK MODE ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #d4af37;
    }
    .product-card {
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #d4af37;
        margin-bottom: 20px;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .profit-badge {
        background-color: rgba(0, 255, 0, 0.1);
        color: #4CAF50;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    .banner {
        background-color: #8b0000;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 30px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .desc-text {
        font-size: 0.9em;
        color: #aaaaaa;
        flex-grow: 1;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DEL CARRITO ---
if "carrito" not in st.session_state:
    st.session_state.carrito = {}

# --- HEADER Y BANNER ---
st.title("🍷 Rojo Malbec | Portal Mayorista")
st.markdown("""
<div class='banner'>
    🌿 CALIDAD PREMIUM ASEGURADA: Producimos a pedido para garantizar máxima frescura. 
    <br>Tiempo estimado de elaboración y envío: 7 días hábiles.
</div>
""", unsafe_allow_html=True)

# --- CARGAR CATÁLOGO ---
with st.spinner("Actualizando catálogo y precios..."):
    df_catalogo = load_catalog_data()

if df_catalogo.empty:
    st.error("No se pudo cargar el catálogo. Por favor contacte a administración.")
    st.stop()

# --- SIDEBAR: CARRITO Y CHECKOUT ---
st.sidebar.title("🛒 Tu Pedido")

if not st.session_state.carrito:
    st.sidebar.info("Tu pedido está vacío. Agregá productos desde el catálogo.")
else:
    total_pedido = 0
    items_carrito = []
    
    for nombre, item_data in st.session_state.carrito.items():
        if item_data['cantidad'] > 0:
            subtotal = item_data['cantidad'] * item_data['precio']
            total_pedido += subtotal
            
            st.sidebar.markdown(f"**{nombre}**")
            cols_cart = st.sidebar.columns([2, 1, 1])
            with cols_cart[0]:
                st.write(f"{item_data['cantidad']} un. x ${item_data['precio']:,}")
            with cols_cart[1]:
                if st.button("➖", key=f"del_{nombre}"):
                    st.session_state.carrito[nombre]['cantidad'] -= 1
                    if st.session_state.carrito[nombre]['cantidad'] <= 0:
                        del st.session_state.carrito[nombre]
                    st.rerun()
            with cols_cart[2]:
                if st.button("➕", key=f"add_{nombre}_cart"):
                    st.session_state.carrito[nombre]['cantidad'] += 1
                    st.rerun()
            st.sidebar.markdown("---")
            
            items_carrito.append({
                'nombre': nombre,
                'cantidad': item_data['cantidad'],
                'precio': item_data['precio'],
                'subtotal': subtotal
            })

    if items_carrito:
        st.sidebar.subheader(f"Total: $ {total_pedido:,}")
        
        st.sidebar.markdown("### 📝 Datos de Envío")
        nombre_cliente = st.sidebar.text_input("Nombre del Local / Distribuidor")
        cuit = st.sidebar.text_input("CUIT (Opcional)")
        direccion = st.sidebar.text_input("Dirección de Envío")
        
        if st.sidebar.button("✅ FINALIZAR Y ENVIAR PEDIDO", type="primary", use_container_width=True):
            if not nombre_cliente:
                st.sidebar.error("Por favor ingresá tu nombre.")
            else:
                link_wa = generar_mensaje_whatsapp(
                    carrito=items_carrito,
                    total_pedido=total_pedido,
                    telefono="5493544308380",
                    datos_cliente={"nombre": nombre_cliente, "cuit": cuit, "direccion": direccion}
                )
                st.sidebar.success("¡Pedido listo!")
                st.sidebar.markdown(f"[📲 Haz clic aquí para enviar por WhatsApp]({link_wa})", unsafe_allow_html=True)
                if st.sidebar.button("Limpiar Carrito"):
                    st.session_state.carrito = {}
                    st.rerun()

# --- CATÁLOGO DE PRODUCTOS ---
st.subheader("Catálogo de Productos")
search = st.text_input("🔍 Buscar blend...")

if search:
    df_catalogo = df_catalogo[df_catalogo["Nombre"].str.contains(search, case=False)]

# Mostrar en grilla de 3 columnas
cols = st.columns(3)
for idx, row in df_catalogo.iterrows():
    nombre = row["Nombre"]
    costo_real = float(row["Precio_Mayorista"])
    pvp_real = float(row["Precio_Venta"])
    
    # Redondeo pedido
    costo_redondeado = redondear_precio(costo_real)
    pvp_redondeado = redondear_precio(pvp_real)
    ganancia_neta = pvp_redondeado - costo_redondeado
    
    desc_path = os.path.join(current_dir, "Descripciones_RojoMalbec.md")
    descripcion = extraer_descripcion(nombre, desc_path)
    
    col_idx = idx % 3
    with cols[col_idx]:
        st.markdown(f"""
        <div class='product-card'>
            <h3 style='margin-top:0;'>{nombre}</h3>
            <p style='margin-bottom:5px;'><b>Costo Compra:</b> $ {costo_redondeado:,}</p>
            <p style='margin-bottom:0;'><b>Precio Sugerido:</b> $ {pvp_redondeado:,}</p>
            <div class='profit-badge'>Ganancia Neta: $ {ganancia_neta:,}</div>
            <div class='desc-text'>{descripcion}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Controles
        c1, c2, c3 = st.columns([1, 1, 1])
        
        qty_actual = st.session_state.carrito.get(nombre, {}).get("cantidad", 0)
        
        with c1:
            if st.button("➖", key=f"minus_{nombre}", use_container_width=True):
                if qty_actual > 0:
                    st.session_state.carrito[nombre]['cantidad'] -= 1
                    if st.session_state.carrito[nombre]['cantidad'] == 0:
                        del st.session_state.carrito[nombre]
                    st.rerun()
        with c2:
            st.markdown(f"<div style='text-align:center; padding-top:5px; font-weight:bold;'>{qty_actual}</div>", unsafe_allow_html=True)
        with c3:
            if st.button("➕", key=f"plus_{nombre}", use_container_width=True):
                if nombre not in st.session_state.carrito:
                    st.session_state.carrito[nombre] = {"cantidad": 1, "precio": costo_redondeado}
                else:
                    st.session_state.carrito[nombre]['cantidad'] += 1
                st.rerun()
        
        st.write("") # Espaciador

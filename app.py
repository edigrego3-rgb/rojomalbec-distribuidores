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
    .stTabs [data-baseweb="tab"] {
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---
def detectar_categoria(nombre_producto):
    nombre = str(nombre_producto).lower()
    if "sal " in nombre or nombre.startswith("sal"):
        return "🧂 Sales"
    elif "vital" in nombre:
        return "💚 Vital"
    elif "blend" in nombre or "bbq" in nombre or "curry" in nombre or "baharat" in nombre or "masala" in nombre or "joe" in nombre or "ranch" in nombre or "pesto" in nombre or "jerk" in nombre:
        return "🌿 Blends"
    elif "té " in nombre or "te " in nombre or "rooibos" in nombre or "karak" in nombre:
        return "🍵 Tés"
    elif "mocktail" in nombre:
        return "🍹 Mocktails"
    elif "pimienta" in nombre:
        return "🌶️ Pimientas"
    else:
        return "🌿 Blends" # Por defecto los mandamos a blends

def buscar_imagen(nombre_producto):
    images_dir = os.path.join(current_dir, "images")
    if not os.path.exists(images_dir):
        return None
        
    term = nombre_producto.replace(" ", "").lower()
    # Casos especiales de nombres que no coinciden exacto
    if "sloopy joe" in nombre_producto.lower(): term = "sloppyjoe"
    
    archivos_encontrados = []
    for f in os.listdir(images_dir):
        if f.endswith(".png"):
            if term in f.replace("_", "").lower():
                archivos_encontrados.append(f)
                
    if not archivos_encontrados:
        return None
        
    # Priorizar la foto frontal (que suele decir "Clean", "Frontal" o "Color")
    for f in archivos_encontrados:
        nombre_lower = f.lower()
        if "clean" in nombre_lower or "frontal" in nombre_lower or "color" in nombre_lower:
            return os.path.join(images_dir, f)
            
    # Si no hay frontal, devolvemos la primera que haya encontrado (ej: Trasera)
    return os.path.join(images_dir, archivos_encontrados[0])

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

df_catalogo["Categoria"] = df_catalogo["Nombre"].apply(detectar_categoria)

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
search = st.text_input("🔍 Buscar blend...")

# Pestañas de categorías
categorias = ["🏠 Todos", "🧂 Sales", "🌿 Blends", "💚 Vital", "🍵 Tés", "🍹 Mocktails", "🌶️ Pimientas"]
tabs = st.tabs(categorias)

for i, tab in enumerate(tabs):
    with tab:
        cat_actual = categorias[i]
        
        # Filtrar datos
        df_tab = df_catalogo.copy()
        if cat_actual != "🏠 Todos":
            df_tab = df_tab[df_tab["Categoria"] == cat_actual]
            
        if search:
            df_tab = df_tab[df_tab["Nombre"].str.contains(search, case=False)]
            
        if df_tab.empty:
            st.info("No hay productos en esta categoría.")
            continue
            
        # Mostrar en grilla de 3 columnas
        cols = st.columns(3)
        for idx, row in df_tab.reset_index(drop=True).iterrows():
            nombre = row["Nombre"]
            costo_real = float(row["Precio_Mayorista"])
            pvp_real = float(row["Precio_Venta"])
            
            # Redondeo pedido
            costo_redondeado = redondear_precio(costo_real)
            pvp_redondeado = redondear_precio(pvp_real)
            ganancia_neta = pvp_redondeado - costo_redondeado
            
            desc_path = os.path.join(current_dir, "Descripciones_RojoMalbec.md")
            descripcion = extraer_descripcion(nombre, desc_path)
            
            imagen_path = buscar_imagen(nombre)
            
            col_idx = idx % 3
            with cols[col_idx]:
                st.markdown("<div class='product-card'>", unsafe_allow_html=True)
                
                # Imagen
                if imagen_path:
                    st.image(imagen_path, use_container_width=True)
                
                # Info
                st.markdown(f"""
                    <h3 style='margin-top:10px;'>{nombre}</h3>
                    <p style='margin-bottom:5px;'><b>Costo Compra:</b> $ {costo_redondeado:,}</p>
                    <p style='margin-bottom:0;'><b>Precio Sugerido:</b> $ {pvp_redondeado:,}</p>
                    <div class='profit-badge'>Ganancia Neta: $ {ganancia_neta:,}</div>
                    <div class='desc-text'>{descripcion}</div>
                """, unsafe_allow_html=True)
                
                # Controles de Carrito
                c1, c2, c3 = st.columns([1, 1, 1])
                qty_actual = st.session_state.carrito.get(nombre, {}).get("cantidad", 0)
                
                with c1:
                    if st.button("➖", key=f"minus_{cat_actual}_{idx}", use_container_width=True):
                        if qty_actual > 0:
                            st.session_state.carrito[nombre]['cantidad'] -= 1
                            if st.session_state.carrito[nombre]['cantidad'] == 0:
                                del st.session_state.carrito[nombre]
                            st.rerun()
                with c2:
                    st.markdown(f"<div style='text-align:center; padding-top:5px; font-weight:bold;'>{qty_actual}</div>", unsafe_allow_html=True)
                with c3:
                    if st.button("➕", key=f"plus_{cat_actual}_{idx}", use_container_width=True):
                        if nombre not in st.session_state.carrito:
                            st.session_state.carrito[nombre] = {"cantidad": 1, "precio": costo_redondeado}
                        else:
                            st.session_state.carrito[nombre]['cantidad'] += 1
                        st.rerun()
                        
                st.markdown("</div>", unsafe_allow_html=True)

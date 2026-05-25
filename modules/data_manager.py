import streamlit as st
import pandas as pd
import gspread

SHEET_NAME = "RojoMalbec DB"

def get_connection():
    if "gsheets_conn" not in st.session_state:
        try:
            creds_dict = {
                "type": st.secrets["gcp_service_account"]["type"],
                "project_id": st.secrets["gcp_service_account"]["project_id"],
                "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
                "private_key": st.secrets["gcp_service_account"]["private_key"],
                "client_email": st.secrets["gcp_service_account"]["client_email"],
                "client_id": st.secrets["gcp_service_account"]["client_id"],
                "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
                "token_uri": st.secrets["gcp_service_account"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
            }
            gc = gspread.service_account_from_dict(creds_dict)
            st.session_state["gsheets_conn"] = gc
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            return None
    return st.session_state["gsheets_conn"]

@st.cache_data(ttl=600) # Caché por 10 minutos para que sea rápido pero actualizado
def load_catalog_data():
    gc = get_connection()
    if not gc:
        return pd.DataFrame()
    
    try:
        sh = gc.open(SHEET_NAME)
        ws = sh.worksheet("recetas")
        raw_data = ws.get_all_values()
        
        if not raw_data:
            return pd.DataFrame()
            
        headers = [str(h).strip() for h in raw_data[0]]
        df = pd.DataFrame(raw_data[1:], columns=headers)
        
        # Filtrar solo columnas necesarias para el B2B
        cols_necesarias = ["Nombre", "Precio_Mayorista", "Precio_Venta"]
        for col in cols_necesarias:
            if col not in df.columns:
                df[col] = 0.0
                
        # Limpiar números
        for col in ["Precio_Mayorista", "Precio_Venta"]:
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
            
        # Filtrar solo los que tienen precio mayorista > 0 (asumiendo que los que no tienen no se venden)
        df = df[df["Precio_Mayorista"] > 0]
        
        return df.sort_values("Nombre")
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return pd.DataFrame()

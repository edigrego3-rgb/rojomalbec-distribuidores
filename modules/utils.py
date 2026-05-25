import urllib.parse
import math
import os
import re

def redondear_precio(valor):
    """Redondea hacia arriba a los 100 pesos más cercanos"""
    if valor <= 0:
        return 0
    return math.ceil(valor / 100.0) * 100

def extraer_descripcion(nombre_blend, filepath="Descripciones_RojoMalbec.md"):
    """
    Busca el nombre del blend en el archivo markdown y extrae su descripción.
    """
    if not os.path.exists(filepath):
        return "Descripción no disponible en este momento."
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            contenido = f.read()
            
        # Buscar el nombre como un título ##
        # Ej: ## Sloopy Joe 🍔 o ## Sal al Malbec 🍷
        patron = re.compile(rf"##\s+.*?{re.escape(nombre_blend)}.*?$.*?(?=\n## |\Z)", re.MULTILINE | re.IGNORECASE | re.DOTALL)
        match = patron.search(contenido)
        
        if match:
            bloque = match.group(0)
            # Limpiar el título y quedarse con el texto principal (primer párrafo post título)
            lineas = bloque.split('\n')
            descripcion_breve = ""
            ingredientes = ""
            
            for linea in lineas[1:]: # saltar el título
                linea = linea.strip()
                if not linea or linea.startswith('---'):
                    continue
                if linea.startswith('**Ingredientes:**'):
                    ingredientes = linea
                elif not linea.startswith('**') and not descripcion_breve:
                    descripcion_breve = linea
                    
            resultado = descripcion_breve
            if ingredientes:
                resultado += f"\n\n{ingredientes}"
            return resultado if resultado else "Una exquisita creación de Rojo Malbec."
    except Exception:
        pass
        
    return "Una creación premium de Rojo Malbec."

def generar_mensaje_whatsapp(carrito, total_pedido, telefono, datos_cliente):
    """
    Genera el link de WhatsApp con el pedido formateado.
    """
    nombre_local = datos_cliente.get("nombre", "Cliente B2B")
    cuit = datos_cliente.get("cuit", "")
    direccion = datos_cliente.get("direccion", "")
    
    texto = f"🌟 *NUEVO PEDIDO ROJO MALBEC* 🌟\n"
    texto += f"🏠 Local: {nombre_local}\n"
    if cuit: texto += f"📋 CUIT: {cuit}\n"
    if direccion: texto += f"📍 Envío: {direccion}\n"
    texto += "\n*DETALLE DEL PEDIDO:*\n"
    
    for item in carrito:
        texto += f"▪️ {item['cantidad']}x {item['nombre']} ($ {item['subtotal']:,})\n"
        
    texto += f"\n💰 *TOTAL A ABONAR:* $ {total_pedido:,}\n"
    texto += "\n_Aguardamos confirmación y datos de transferencia. ¡Gracias!_"
    
    texto_codificado = urllib.parse.quote(texto)
    # Asegurar formato internacional del teléfono (remover + si existe)
    tel_limpio = telefono.replace("+", "").replace(" ", "")
    
    return f"https://wa.me/{tel_limpio}?text={texto_codificado}"

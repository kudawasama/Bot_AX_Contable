"""
Utilidades para identificación y normalización de IDs de diario.
"""

import re
import os

# Nombres cortos para mostrar en logs (en vez de rutas largas de archivo)
NOMBRES_IMAGENES = {
    "btn_registrar_menu.png": "Menu",
    "btn_registrar_confirm.png": "Confirmar",
    "checkbox_vacio.png": "Checkbox",
    "check_usuario_marcado.png": "Check-Marcado",
    "Error_Registro.png": "Error-Ventana",
    "Avanzar_Abajo.png": "Scroll",
    "Formularios_Abiertos.png": "FormAbierto",
    "msg_exito_asiento_1.png": "Exito-Ventana",
    "btn_cerrar_info.png": "Cerrar",
}


def nombre_corto(ruta):
    """Devuelve el nombre corto de una imagen para mostrar en logs."""
    base = os.path.basename(ruta)
    return NOMBRES_IMAGENES.get(base, base)


def normalizar_id_diario(id_ocr):
    """
    Normaliza un ID de diario leído por OCR a su forma canónica.

    Extrae la parte numérica central (ignorando prefijos como IS/iS/1S/VS/vS
    y sufijos como iat/Diat/iar/Diar/Diai/Dial) y la devuelve en mayúsculas.

    Ejemplos:
        'IS00327946iat' -> '00327946'
        'iS00327946Diai' -> '00327946'
        '1S00326946Diat' -> '00326946'
        'VS00325150Dia' -> '00325150'
        '00327946' -> '00327946'
    """
    digitos = re.findall(r'\d{6,}', id_ocr)
    if digitos:
        return digitos[0]
    # Fallback: limpiar y devolver tal cual en mayúsculas
    return id_ocr.strip().upper()

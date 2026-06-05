"""
Tests para normalizar_id_diario.

Ejecutar con: python -m pytest tests/test_vision.py -v
Requiere definir BOT_AX_TEST_MODE=1 para saltar import de pyautogui.
"""
import os

# Modo test: evitar import de pyautogui
os.environ["BOT_AX_TEST_MODE"] = "1"

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Ahora vision.py no fallará porque pyautogui ya está mockeado
import importlib
import vision

# Sobrescribir pyautogui para que no falle
import types
vision.pyautogui = types.ModuleType("pyautogui")


class TestNormalizarIdDiario:
    """Pruebas unitarias para normalizar_id_diario()."""

    def test_formato_completo_mayusculas(self):
        assert vision.normalizar_id_diario("IS00327946iat") == "00327946"

    def test_formato_minusculas_prefijo(self):
        assert vision.normalizar_id_diario("iS00327946Diai") == "00327946"

    def test_prefijo_con_uno(self):
        assert vision.normalizar_id_diario("1S00326946Diat") == "00326946"

    def test_prefijo_vs(self):
        assert vision.normalizar_id_diario("VS00325150Dia") == "00325150"

    def test_solo_digitos(self):
        assert vision.normalizar_id_diario("00327946") == "00327946"

    def test_id_desconocido(self):
        assert vision.normalizar_id_diario("DESCONOCIDO") == "DESCONOCIDO"

    def test_error_lectura(self):
        assert vision.normalizar_id_diario("ERROR_LECTURA") == "ERROR_LECTURA"

    def test_vacio(self):
        assert vision.normalizar_id_diario("") == ""

    def test_caso_real_00326946(self):
        variantes = [
            "IS00326946iat", "IS00326946Diat", "IS00326946iar",
            "IS00326946Diai", "iS00326946Diai",
        ]
        for v in variantes:
            assert vision.normalizar_id_diario(v) == "00326946", f"Fallo con: {v}"

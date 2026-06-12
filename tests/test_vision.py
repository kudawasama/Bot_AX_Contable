"""
Tests para normalizar_id_diario.

Ejecutar con: python -m pytest tests/ -v
Usa conftest.py para fixtures compartidos.

Importa directamente desde bot_ax.vision.ids para evitar
dependencias con pyautogui/pytesseract (ids.py no los necesita).
"""

from bot_ax.vision.ids import normalizar_id_diario


class TestNormalizarIdDiario:
    """Pruebas unitarias para normalizar_id_diario()."""

    def test_formato_completo_mayusculas(self):
        assert normalizar_id_diario("IS00327946iat") == "00327946"

    def test_formato_minusculas_prefijo(self):
        assert normalizar_id_diario("iS00327946Diai") == "00327946"

    def test_prefijo_con_uno(self):
        assert normalizar_id_diario("1S00326946Diat") == "00326946"

    def test_prefijo_vs(self):
        assert normalizar_id_diario("VS00325150Dia") == "00325150"

    def test_solo_digitos(self):
        assert normalizar_id_diario("00327946") == "00327946"

    def test_id_desconocido(self):
        assert normalizar_id_diario("DESCONOCIDO") == "DESCONOCIDO"

    def test_error_lectura(self):
        assert normalizar_id_diario("ERROR_LECTURA") == "ERROR_LECTURA"

    def test_vacio(self):
        assert normalizar_id_diario("") == ""

    def test_caso_real_00326946(self):
        variantes = [
            "IS00326946iat", "IS00326946Diat", "IS00326946iar",
            "IS00326946Diai", "iS00326946Diai",
        ]
        for v in variantes:
            assert normalizar_id_diario(v) == "00326946", f"Fallo con: {v}"

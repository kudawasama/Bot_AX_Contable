"""Tests unitarios de la normalización de IDs de diario.

Módulo bajo prueba: ``src/services/vision.py`` → ``normalizar_id_diario()``.

Corrección (hallazgo C-1 del plan de implementación): este archivo hacía
``import vision`` (estructura previa al refactor modular ``2aad23d``), lo que
rompía la colección de pytest. Ahora importa el módulo real desde
``src.services.vision`` y ya no requiere ``BOT_AX_TEST_MODE`` ni la mutación
manual de ``types.ModuleType`` (los dobles inertes viven en ``tests/conftest.py``).

Ejecutar con: ``python -m pytest tests/test_vision.py -v``
"""

from src.services.vision import normalizar_id_diario


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

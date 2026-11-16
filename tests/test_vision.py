"""Tests unitarios de la normalización de IDs de diario.

Módulo bajo prueba: ``src/services/vision.py`` → ``normalizar_id_diario()``.

Corrección (hallazgo C-1 del plan de implementación): este archivo hacía
``import vision`` (estructura previa al refactor modular ``2aad23d``), lo que
rompía la colección de pytest. Ahora importa el módulo real desde
``src.services.vision`` y ya no requiere ``BOT_AX_TEST_MODE`` ni la mutación
manual de ``types.ModuleType`` (los dobles inertes viven en ``tests/conftest.py``).

Ejecutar con: ``python -m pytest tests/test_vision.py -v``
"""

from src.services.vision import leer_id_diario, normalizar_id_diario


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


class TestLecturaIdDiarioValidada:
    """B1: el ID de AX tiene exactamente 8 dígitos y se valida antes de usarlo.

    Antes, ``leer_id_diario`` devolvía cualquier texto del OCR y el motor procesaba el
    diario con ese identificador: un dígito mal leído hacía registrar —y listar como
    error— un diario distinto del real.
    """

    def test_lee_el_id_valido_de_8_digitos(self, mock_tesseract):
        mock_tesseract.image_to_string.return_value = "W00337505Diar"
        assert leer_id_diario((100, 100)) == "00337505"

    def test_basura_del_ocr_no_es_id(self, mock_tesseract):
        mock_tesseract.image_to_string.return_value = "W00ab919Diat"
        assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

    def test_lectura_de_7_digitos_no_es_valida(self, mock_tesseract):
        mock_tesseract.image_to_string.return_value = "W0337501Diat"
        assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

    def test_lectura_corrida_de_9_digitos_no_es_valida(self, mock_tesseract):
        """9 dígitos seguidos: tomar los primeros 8 daría un ID inventado."""
        mock_tesseract.image_to_string.return_value = "W003375050Diar"
        assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

    def test_dos_ids_distintos_en_la_misma_lectura_es_dudoso(self, mock_tesseract):
        mock_tesseract.image_to_string.return_value = "00337505 00337506"
        assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

    def test_dos_ids_aunque_sean_iguales_son_dudosos(self, mock_tesseract):
        """El filtro de OCR quita los separadores: dos IDs quedan como 16 dígitos corridos.

        Es deliberado: ante cualquier lectura que no sea UN único número de 8 dígitos se
        prefiere saltar el diario antes que arriesgar un identificador inventado.
        """
        mock_tesseract.image_to_string.return_value = "00337505 00337505"
        assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

    def test_lectura_vacia_es_error(self, mock_tesseract):
        mock_tesseract.image_to_string.return_value = ""
        assert leer_id_diario((100, 100)) == "ERROR_LECTURA"

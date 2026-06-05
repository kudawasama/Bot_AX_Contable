"""
Tests para el módulo config.py (funciones de configuración).
"""
import sys
import os
import json
import tempfile

# Agregar el directorio del proyecto al path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config


class TestCargarConfiguracion:
    """Pruebas unitarias para cargar_configuracion()."""

    def test_config_valida_se_carga(self):
        """Configuración con sectores válidos debe cargarse correctamente."""
        data = {
            "sector_a": [10, 20, 100, 200],
            "sector_b": [30, 40, 50, 60],
            "sector_scroll": [5, 5, 20, 20],
            "ocr_region_offset": [-275, -13, 110, 28],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            original = config.CONFIG_FILE
            config.CONFIG_FILE = temp_path
            result = config.cargar_configuracion()
            assert result == data
        finally:
            config.CONFIG_FILE = original
            os.unlink(temp_path)

    def test_falta_sector_b(self):
        """Configuración sin sector_b debe retornar None."""
        data = {"sector_a": [10, 20, 100, 200]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            original = config.CONFIG_FILE
            config.CONFIG_FILE = temp_path
            result = config.cargar_configuracion()
            assert result is None
        finally:
            config.CONFIG_FILE = original
            os.unlink(temp_path)

    def test_formato_incorrecto_no_lista(self):
        """Sector que no es lista debe retornar None."""
        data = {"sector_a": "no_es_lista", "sector_b": [1, 2, 3, 4]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            original = config.CONFIG_FILE
            config.CONFIG_FILE = temp_path
            result = config.cargar_configuracion()
            assert result is None
        finally:
            config.CONFIG_FILE = original
            os.unlink(temp_path)

    def test_coordenadas_parciales(self):
        """Lista con menos de 4 elementos debe retornar None."""
        data = {"sector_a": [10, 20], "sector_b": [1, 2, 3, 4]}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            original = config.CONFIG_FILE
            config.CONFIG_FILE = temp_path
            result = config.cargar_configuracion()
            assert result is None
        finally:
            config.CONFIG_FILE = original
            os.unlink(temp_path)

    def test_json_invalido(self):
        """Archivo con JSON malformado debe retornar None."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("esto no es json{{{")
            temp_path = f.name
        try:
            original = config.CONFIG_FILE
            config.CONFIG_FILE = temp_path
            result = config.cargar_configuracion()
            assert result is None
        finally:
            config.CONFIG_FILE = original
            os.unlink(temp_path)

    def test_archivo_inexistente(self):
        """Archivo que no existe debe retornar None."""
        original = config.CONFIG_FILE
        config.CONFIG_FILE = "/ruta/inexistente/config.json"
        try:
            result = config.cargar_configuracion()
            assert result is None
        finally:
            config.CONFIG_FILE = original


class TestObtenerOffsetOcr:
    """Pruebas unitarias para obtener_offset_ocr()."""

    def test_offset_desde_config(self):
        """Debe leer el offset desde la configuración."""
        data = {
            "sector_a": [10, 20, 100, 200],
            "sector_b": [30, 40, 50, 60],
            "ocr_region_offset": [-300, -10, 120, 30],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            temp_path = f.name
        try:
            original = config.CONFIG_FILE
            config.CONFIG_FILE = temp_path
            result = config.obtener_offset_ocr()
            assert result == (-300, -10, 120, 30)
        finally:
            config.CONFIG_FILE = original
            os.unlink(temp_path)

    def test_offset_fallback_sin_config(self):
        """Sin config debe devolver fallback (-275, -13, 110, 28)."""
        result = config.obtener_offset_ocr(config={})
        assert result == (-275, -13, 110, 28)

    def test_offset_fallback_sin_archivo(self):
        """Sin archivo debe devolver fallback."""
        original = config.CONFIG_FILE
        config.CONFIG_FILE = "/ruta/inexistente/config.json"
        try:
            result = config.obtener_offset_ocr()
            assert result == (-275, -13, 110, 28)
        finally:
            config.CONFIG_FILE = original

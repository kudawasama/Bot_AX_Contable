"""Pruebas de la retención de capturas de error (tarea B3 del plan).

``capturar_pantalla_error`` guarda una captura por error; sin límite, ``logs/capturas/``
crece sin control dentro de Google Drive. Estas pruebas ejercitan el rotador **directamente**
sobre un directorio temporal (nunca tocan la carpeta real del proyecto).
"""

import os
from pathlib import Path

from src.services.vision import MAX_CAPTURAS_ERROR, _rotar_capturas


def _crear_capturas(directorio: Path, cantidad: int) -> None:
    """Crea capturas falsas con fecha de modificación creciente (la más nueva, al final)."""
    for indice in range(cantidad):
        archivo: Path = directorio / f"error_003375{indice:02d}_2026-10-13_1200{indice:02d}.png"
        archivo.write_bytes(b"captura falsa")
        momento: float = 1_000_000.0 + indice
        os.utime(archivo, (momento, momento))


class TestRotacionDeCapturas:
    """B3: el directorio de capturas se mantiene acotado."""

    def test_el_maximo_por_defecto_es_50(self):
        assert MAX_CAPTURAS_ERROR == 50

    def test_conserva_las_50_mas_recientes(self, tmp_path: Path):
        _crear_capturas(tmp_path, 55)

        _rotar_capturas(tmp_path, max_archivos=50)

        restantes = sorted(tmp_path.glob("error_*.png"))
        assert len(restantes) == 50
        nombres = {archivo.name for archivo in restantes}
        for indice in range(5):  # las 5 más antiguas (0..4) se eliminaron
            assert f"error_003375{indice:02d}_" not in " ".join(nombres)

    def test_deja_intacta_una_carpeta_por_debajo_del_maximo(self, tmp_path: Path):
        _crear_capturas(tmp_path, 10)

        _rotar_capturas(tmp_path, max_archivos=50)

        assert len(list(tmp_path.glob("error_*.png"))) == 10

    def test_solo_toca_las_capturas_de_error(self, tmp_path: Path):
        (tmp_path / "otro_archivo.png").write_bytes(b"no tocar")
        _crear_capturas(tmp_path, 55)

        _rotar_capturas(tmp_path, max_archivos=50)

        assert (tmp_path / "otro_archivo.png").exists()

    def test_carpeta_inexistente_no_rompe(self, tmp_path: Path):
        _rotar_capturas(tmp_path / "no_existe", max_archivos=50)  # no debe levantar

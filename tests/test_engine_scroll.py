"""Pruebas del control de scroll y del avance de pantalla en AX.

POR QUÉ EXISTEN (incidente 2026-11-18):
    El bot terminaba la ejecución ("No se encontraron más diarios") con diarios todavía
    pendientes más abajo. La causa: `intentos_scroll` contaba CUALQUIER vuelta sin
    candidato, y como la lista negra tiene decenas de diarios, tres pantallas seguidas de
    diarios ya listados bastaban para cerrar la sesión. Evidencia: la sesión de las 21:35
    cerró por esa vía y a las 22:10, tras unos scrolls más, apareció 00342122.

    Ahora el contador mide "scrolls seguidos SIN que la lista se mueva", usando como ancla
    el ID del diario visible más arriba.

    Son pruebas puras: no capturan pantalla ni mueven el mouse.
"""
from typing import Optional

from src.core.engine import (
    MAX_INTENTOS_SIN_MOVIMIENTO,
    MAX_SCROLLS_POR_CICLO,
    TIMEOUT_RESULTADO_SEGUNDOS,
    _actualizar_intentos_scroll,
)
from src.services.vision import _expandir_region


def test_la_lista_que_se_mueve_no_cuenta_como_intento_fallido() -> None:
    """Si el ancla cambia hay filas nuevas: el contador vuelve a cero."""
    assert _actualizar_intentos_scroll("00342122", "00342117", 2) == 0


def test_la_lista_quieta_suma_intentos() -> None:
    """Si el ancla se repite, la pantalla no se movió: cuenta como intento fallido."""
    assert _actualizar_intentos_scroll("00342122", "00342122", 0) == 1
    assert _actualizar_intentos_scroll("00342122", "00342122", 2) == 3


def test_primer_scroll_del_ciclo_nunca_cuenta() -> None:
    """Sin ancla anterior no hay comparación posible: no se da la lista por terminada."""
    assert _actualizar_intentos_scroll("00342122", None, 0) == 0


def test_lectura_dudosa_no_termina_la_ejecucion() -> None:
    """Un OCR malo (ancla ilegible) no debe cerrar la sesión por sí solo."""
    assert _actualizar_intentos_scroll(None, "00342122", 2) == 0


def test_los_topos_permiten_llegar_al_final_real_de_la_lista() -> None:
    """Los topes son coherentes: se dan por terminados 3 scrolls sin movimiento."""
    assert MAX_INTENTOS_SIN_MOVIMIENTO == 3
    assert MAX_SCROLLS_POR_CICLO > MAX_INTENTOS_SIN_MOVIMIENTO


def test_el_timeout_del_resultado_cubre_los_registros_reales() -> None:
    """La espera máxima supera el registro más lento medido (824 s) con margen."""
    assert TIMEOUT_RESULTADO_SEGUNDOS >= 1200


def test_expandir_region_contiene_el_patron() -> None:
    """Una región corta por 1 px se amplía lo justo para contener el patrón (sector_b 31 vs 32)."""
    region = (1106, 79, 251, 31)
    x, y, w, h = _expandir_region(region, 148, 32)
    assert h >= 32 and w >= 148
    # Conserva el centro original (no desplaza la búsqueda a otra zona de la pantalla)
    centro_x_original: Optional[float] = region[0] + region[2] / 2
    centro_y_original: Optional[float] = region[1] + region[3] / 2
    assert abs((x + w / 2) - centro_x_original) <= 1
    assert abs((y + h / 2) - centro_y_original) <= 1


def test_expandir_region_no_sale_de_la_pantalla() -> None:
    """La región ampliada nunca tiene coordenadas negativas."""
    x, y, _, _ = _expandir_region((0, 0, 10, 10), 40, 40)
    assert x >= 0 and y >= 0

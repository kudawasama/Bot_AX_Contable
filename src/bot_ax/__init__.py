"""
Bot AX Contable — Automatización para Microsoft Dynamics AX.

Registro automático de diarios contables mediante
reconocimiento de imágenes (template matching) y OCR (Tesseract).
"""

from bot_ax._version import __version__, VERSION_TAG, get_git_short_sha

__all__ = ["__version__", "VERSION_TAG", "get_git_short_sha"]

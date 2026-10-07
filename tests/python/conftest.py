"""Configuración común de los tests de Python: da acceso al motor de python/."""
import os
import sys

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "python"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

"""Rejillas de casos compartidas por los tests (y por la prueba de paridad con JS)."""
import itertools
import os

from datos import TABLES

RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
from modelos import MODEL_KEYS

TOL_ID = 1e-12      # identidades exactas, salvo redondeo de coma flotante
TOL_PARIDAD = 1e-8  # Python frente a JS (CLAUDE.md §4); relativa si |valor| > 1

TABLAS = list(TABLES)
SEXOS = ("M", "H")
METODOS = ("lin", "exp")
MODELOS = list(MODEL_KEYS)

# Edades enteras y no enteras, incluidas las cercanas a ω
EDADES = (0, 0.5, 17, 30, 47.3, 65, 85.75, 100, 110.5, 119, 120)
PLAZOS = (0, 1, 2.5, 10, 30)          # n
DIFERIMIENTOS = (0, 1, 5.25, 20)      # m
AÑOS = (1960, 2026, 2100)             # solo afecta a las generacionales


def casos_tablas(reducido=False):
    """(tabla, sexo, año, método, x, n, m)."""
    edades = EDADES[::2] if reducido else EDADES
    for key, sex, met in itertools.product(TABLAS, SEXOS, METODOS):
        años = AÑOS if TABLES[key]["kind"] == "per" else (2026,)
        for año, x, n, m in itertools.product(años, edades, PLAZOS, DIFERIMIENTOS):
            yield key, sex, año, met, x, n, m


COMBOS_RENTAS = [("pasem_gen_2", "M"), ("per_ind_2", "H"), ("per_col_1", "M"), ("pasem_dec_1", "H")]


def casos_rentas(combos=COMBOS_RENTAS):
    """(tabla, sexo, año, x, n, m, k, I, c, pre, vitalicia) válidos según rentas.validar
    y rentas.validar_tabla (l_x > 0)."""
    import rentas
    for (key, sex), x, m, k, n, I, pre, vit in itertools.product(
            combos, (0, 40, 65, 100, 108, 119, 120), (1, 4, 12), (0, 2.5, 10),
            (1, 25.5), (0.0, 0.0195, 0.05), (True, False), (True, False)):
        if vit and n != 1:      # en la vitalicia n no interviene: basta un valor
            continue
        if rentas.validar(x, n, m, k, I, 1.0, vit) is None and rentas.validar_tabla(key, sex, 2026, x) is None:
            yield key, sex, 2026, x, n, m, k, I, 1.0, pre, vit


def cerca(a, b, tol):
    """|a − b| ≤ tol · máx(1, |a|, |b|); dos NaN (o None) se consideran iguales."""
    import math
    na = a is None or (isinstance(a, float) and math.isnan(a))
    nb = b is None or (isinstance(b, float) and math.isnan(b))
    if na or nb:
        return na and nb
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))

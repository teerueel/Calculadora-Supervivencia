"""Paridad Python/JS: los dos motores dan los mismos números (tolerancia 1e-8, CLAUDE.md §4).

Python prepara los casos, tests/js/volcado.mjs los calcula con el motor web y aquí se comparan.
"""
import itertools
import json
import math
import os
import shutil
import subprocess

import pytest

import modelos
import rentas
import tablas
from casos import (RAIZ_REPO, TABLAS, SEXOS, METODOS, MODELOS, EDADES, PLAZOS, DIFERIMIENTOS,
                   TOL_PARIDAD, casos_tablas, casos_rentas, cerca)
from datos import TABLES

VALIDAR = [
    (30, 10, 12, 0, 0.02, 1, False, False, 2026),
    (30.5, 10, 1, 0, 0.02, 1, False, False, 2026),
    (121, 10, 1, 0, 0.02, 1, False, False, 2026),
    (30, 10, 0, 0, 0.02, 1, False, False, 2026),
    (30, 10, 4, 0.3, 0.02, 1, False, False, 2026),
    (30, 10.1, 4, 0, 0.02, 1, False, False, 2026),
    (30, 0, 1, 0, 0.02, 1, False, False, 2026),
    (100, 0, 1, 21, 0.02, 1, True, False, 2026),
    (30, 10, 1, 0, -1, 1, False, False, 2026),
    (30, 10, 1, 0, 0.02, 0, False, False, 2026),
    (30, 10, 1, 0, 0.02, 1, False, True, 1800),
    (30, 10, 1, 0, 0.02, 1, False, True, 2026.5),
]
VALIDAR_TABLA = [(k, s, 2026, x) for k in TABLAS for s in SEXOS for x in (0, 104, 109, 110, 111, 112, 119, 120)]
FRAC = [(p, m) for m in (1, 2, 4, 12) for p in (0, 1, 5, 12, 13, 47, 100)]


MAX_DIF = {}  # mayor diferencia relativa observada por sección (informativo)


def preparar_casos():
    return dict(
        datos=True, presets=True,
        vectores=[(k, s, c) for k in TABLAS for s in SEXOS for c in ((1900, 1960, 2026, 2100) if tablas.is_per(k) else (0,))],
        tablas=list(casos_tablas()),
        modelos=[(k, s, met, x, n, m) for k, s, met in itertools.product(MODELOS, SEXOS, METODOS)
                 for x, n, m in itertools.product(EDADES, PLAZOS, DIFERIMIENTOS)],
        rentas=list(casos_rentas())[::4],
        validar=VALIDAR, validarTabla=VALIDAR_TABLA, frac=FRAC,
    )


def ejecutar_js(casos):
    node = shutil.which("node")
    assert node, "No se encuentra Node.js en el PATH: es necesario para la prueba de paridad."
    script = os.path.join(RAIZ_REPO, "tests", "js", "volcado.mjs")
    r = subprocess.run([node, script], input=json.dumps(casos), capture_output=True, text=True,
                       encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def casos():
    return preparar_casos()


@pytest.fixture(scope="module")
def js(casos):
    return ejecutar_js(casos)


def comparar(nombre, py, js_, fallos):
    if isinstance(py, dict):
        assert set(map(str, py)) == set(js_), (nombre, sorted(map(str, py)), sorted(js_))
        for k, v in py.items():
            comparar(f"{nombre}.{k}", v, js_[str(k)], fallos)
    elif isinstance(py, (list, tuple)):
        assert len(py) == len(js_), (nombre, len(py), len(js_))
        for i, (a, b) in enumerate(zip(py, js_)):
            comparar(f"{nombre}[{i}]", a, b, fallos)
    elif isinstance(py, (int, float)) and not isinstance(py, bool):
        if not cerca(float(py), None if js_ is None else float(js_), TOL_PARIDAD):
            fallos.append((nombre, py, js_))
        elif js_ is not None and math.isfinite(py):
            sec = nombre.split("-")[0].split(".")[0].split("[")[0]
            d = abs(py - js_) / max(1.0, abs(py))
            MAX_DIF[sec] = max(MAX_DIF.get(sec, 0.0), d)
    else:
        if py != js_:
            fallos.append((nombre, py, js_))


def test_datos_de_las_tablas(js):
    fallos = []
    comparar("TABLES", {k: t["data"] for k, t in TABLES.items()}, js["datos"], fallos)
    assert not fallos, fallos[:5]


def test_presets_de_los_modelos(js):
    fallos = []
    comparar("PRESETS", {k: modelos.PRESETS[k] for k in MODELOS}, js["presets"], fallos)
    assert not fallos, fallos[:5]


def test_vectores_q_y_l(casos, js):
    fallos = []
    for (k, s, c), r in zip(casos["vectores"], js["vectores"]):
        q = tablas.mortality_vector(k, s, c)
        comparar(f"{k}-{s}-{c}", {"q": q, "l": tablas.build_lx(q)}, r, fallos)
    assert not fallos, fallos[:5]


def test_tablas(casos, js):
    fallos = []
    for (k, s, año, met, x, n, m), r in zip(casos["tablas"], js["tablas"]):
        p = tablas.compute(k, s, x, n, m, año, met)
        comparar(f"{k}-{s}-{año}-{met}-x{x}-n{n}-m{m}", {c: p[c] for c in r}, r, fallos)
    assert len(js["tablas"]) == len(casos["tablas"])
    assert not fallos, fallos[:5]


def test_modelos(casos, js):
    fallos = []
    for (k, s, met, x, n, m), r in zip(casos["modelos"], js["modelos"]):
        E = modelos.Evaluator(k, modelos.default_params(k, s), met)
        p = E.compute(x, n, m)
        p["mu"] = E.mu(x)
        r = {c: v for c, v in r.items() if c != "ex"}   # e_x abreviada solo existe en la web
        comparar(f"{k}-{s}-{met}-x{x}-n{n}-m{m}", {c: p[c] for c in r}, r, fallos)
    assert not fallos, fallos[:5]


def test_rentas(casos, js):
    fallos = []
    for c, r in zip(casos["rentas"], js["rentas"]):
        D = rentas.calcular(*c, ordenes=(1, 2, 3, 4))
        py = dict(rows=[[f["pagos"], f["val"], f["prob"]] for f in D["rows"]], momentos=D["momentos"],
                  metricas=D["metricas"], N=D["N"], n=D["n"], k=D["k"], cohort=D["cohort"])
        comparar(str(c), py, r, fallos)
    assert len(js["rentas"]) > 50
    assert not fallos, fallos[:5]


def test_validaciones_y_formato(casos, js):
    py = [rentas.validar(x, n, m, k, I, c, vit, ny, y) for x, n, m, k, I, c, vit, ny, y in casos["validar"]]
    assert py == js["validar"]
    assert [rentas.validar_tabla(*a) for a in casos["validarTabla"]] == js["validarTabla"]
    assert [rentas.frac(p, m) for p, m in casos["frac"]] == js["frac"]

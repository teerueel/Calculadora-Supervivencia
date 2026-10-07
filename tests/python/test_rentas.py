"""Rentas actuariales: distribución del valor actual, prima pura y métricas."""
import pytest

import rentas
import tablas
from casos import TOL_ID, COMBOS_RENTAS, casos_rentas

IDS = [f"{k}-{s}" for k, s in COMBOS_RENTAS]


def valor_actuarial(c):
    """Prima pura calculada directamente, sin pasar por la distribución:
    prepagable  ₖ|ä⁽ᵐ⁾ₓ:ₙ⌉ = Σ_{j=0}^{N−1} v^{k+j/m} · _{k+j/m} pₓ / m
    postpagable ₖ|a⁽ᵐ⁾ₓ:ₙ⌉ = Σ_{j=1}^{N}   v^{k+j/m} · _{k+j/m} pₓ / m      (por C = m·c)"""
    key, sex, año, x, n, m, k, I, cuantia, pre, vit = c
    q = tablas.mortality_vector(key, sex, año - x if tablas.is_per(key) else 0)
    l = tablas.build_lx(q)
    N = (rentas.W + 1 - x) * m - round(k * m) if vit else round(n * m)
    v = 1 / (1 + I)
    js = range(0, N) if pre else range(1, N + 1)
    lx = tablas.l_at(l, x, "lin")
    tot = sum(v ** (k + j / m) * tablas.l_at(l, x + k + j / m, "lin") / lx for j in js) / m
    return m * cuantia * tot


def test_hay_casos_suficientes():
    casos = list(casos_rentas())
    assert len(casos) > 300
    assert any(c[-1] for c in casos) and any(not c[-1] for c in casos)


@pytest.mark.parametrize("combo", COMBOS_RENTAS, ids=IDS)
def test_distribucion(combo):
    """Probabilidades ≥ 0 que suman 1; valores crecientes; media = prima pura directa."""
    fallos = []
    for c in casos_rentas([combo]):
        D = rentas.calcular(*c, ordenes=(1, 2))
        probs = [r["prob"] for r in D["rows"]]
        vals = [r["val"] for r in D["rows"]]
        va = valor_actuarial(c)
        if min(probs) < -TOL_ID:
            fallos.append(("prob < 0", c))
        if abs(sum(probs) - 1) > 1e-12:
            fallos.append(("Σ prob ≠ 1", c, sum(probs)))
        if any(b < a - 1e-12 for a, b in zip(vals, vals[1:])):
            fallos.append(("valores no crecientes", c))
        if abs(D["metricas"]["media"] - va) > 1e-12 * max(1.0, va):
            fallos.append(("media ≠ prima pura", c, D["metricas"]["media"], va))
    assert not fallos, fallos[:5]


@pytest.mark.parametrize("combo", COMBOS_RENTAS, ids=IDS)
def test_metricas(combo):
    fallos = []
    for c in casos_rentas([combo]):
        D = rentas.calcular(*c, ordenes=(1, 2, 3, 4))
        M, mom, rows = D["metricas"], D["momentos"], D["rows"]
        cs = [M["cuantiles"][a] for a in rentas.PCTS]
        vmax = max(r["val"] for r in rows if r["prob"] > 0)
        ok = (M["var"] >= 0
              and abs(M["sd"] ** 2 - M["var"]) <= 1e-9 * max(1.0, M["var"])
              and abs(M["var"] - (mom[2] - mom[1] ** 2)) <= 1e-9 * max(1.0, mom[2])
              and all(b >= a for a, b in zip(cs, cs[1:]))
              and M["var995"] == M["cuantiles"][0.995]
              and M["var995"] - 1e-9 <= M["tvar995"] <= vmax + 1e-9
              and (M["sd"] == 0 or (M["curt"] >= 1 - 1e-9 and abs(M["cv"] - M["sd"] / M["media"]) < 1e-12)))
        if not ok:
            fallos.append(c)
    assert not fallos, fallos[:5]


def test_casos_triviales():
    # Prepagable, k = 0, n = 1, m = 1: un único pago seguro de C al inicio.
    D = rentas.calcular("pasem_gen_2", "M", 2026, 40, 1, 1, 0, 0.03, 250.0, True, False)
    assert len(D["rows"]) == 1 and D["rows"][0]["val"] == 250.0 and abs(D["rows"][0]["prob"] - 1) < TOL_ID
    # Prepagable menos postpagable (k = 0): (C/m)·(1 − vⁿ ₙpₓ)
    args = ("per_col_2", "H", 2026, 50, 10, 12, 0, 0.02, 1.0)
    pre = rentas.calcular(*args, True, False)["metricas"]["media"]
    post = rentas.calcular(*args, False, False)["metricas"]["media"]
    npx = tablas.compute("per_col_2", "H", 50, 10, 0, 2026)["npx"]
    assert abs((pre - post) - (12 * 1.0 / 12) * (1 - 1.02 ** -10 * npx)) < 1e-12


def test_lx_nula_es_error():
    """PASEM General: q_110 = 1, luego l_111 = 0 → error, no resultado."""
    assert rentas.validar_tabla("pasem_gen_2", "M", 2026, 110) is None
    assert "lₓ = 0" in rentas.validar_tabla("pasem_gen_2", "M", 2026, 111)
    with pytest.raises(ValueError):
        rentas.calcular("pasem_gen_2", "M", 2026, 111, 1, 1, 0, 0.02, 1.0, True, False)


@pytest.mark.parametrize("args,trozo", [
    ((30.5, 10, 1, 0, 0.02, 1, False), "edad x"),
    ((121, 10, 1, 0, 0.02, 1, False), "edad x"),
    ((30, 10, 0, 0, 0.02, 1, False), "pagos al año"),
    ((30, 10, 4, 0.3, 0.02, 1, False), "diferimiento k"),
    ((30, 10.1, 4, 0, 0.02, 1, False), "horizonte n"),
    ((30, 0, 1, 0, 0.02, 1, False), "horizonte n"),
    ((100, 0, 1, 21, 0.02, 1, True), "nadie llega a cobrar"),
    ((30, 10, 1, 0, -1, 1, False), "tipo de interés"),
    ((30, 10, 1, 0, 0.02, 0, False), "cuantía"),
])
def test_validacion(args, trozo):
    assert trozo in rentas.validar(*args)


def test_validacion_año():
    assert "año" in rentas.validar(30, 10, 1, 0, 0.02, 1, False, need_year=True, year=1800)
    assert rentas.validar(30, 10, 1, 0, 0.02, 1, False, need_year=True, year=2026) is None

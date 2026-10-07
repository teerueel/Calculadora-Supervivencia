"""Seguros de vida: distribución del valor actual Z, prima pura, recargo y métricas."""
import pytest

import distribucion
import rentas
import seguros
import tablas
from casos import TOL_ID, COMBOS_SEGUROS, casos_seguros

IDS = [f"{k}-{s}" for k, s in COMBOS_SEGUROS]


def _l(key, sex, año, x):
    return tablas.build_lx(tablas.mortality_vector(key, sex, año - x if tablas.is_per(key) else 0))


def prima_conmutacion(c):
    """Prima pura por funciones de conmutación, sin pasar por la distribución:
    D_y = v^y l_y,  C_y = v^{y+1} d_y,  M_y = Σ_{z ≥ y} C_z.
      temporal C_f (M_{x+m} − M_{x+m+n})/D_x;  vida entera C_f M_{x+m}/D_x;
      capital diferido C_s D_{x+n}/D_x;  mixto C_f (M_{x+m} − M_{x+m+n})/D_x + C_s D_{x+m+n}/D_x."""
    key, sex, año, tipo, x, n, m, I, Cf, Cs = c
    l = _l(key, sex, año, x)
    v = 1 / (1 + I)
    ly = lambda y: l[y] if 0 <= y < len(l) else 0.0  # noqa: E731
    D = lambda y: v ** y * ly(y)  # noqa: E731
    M = lambda y: sum(v ** (z + 1) * (ly(z) - ly(z + 1)) for z in range(y, len(l)))  # noqa: E731
    if tipo == "temporal":
        return Cf * (M(x + m) - M(x + m + n)) / D(x)
    if tipo == "vida_entera":
        return Cf * M(x + m) / D(x)
    if tipo == "capital_diferido":
        return Cs * D(x + n) / D(x)
    return Cf * (M(x + m) - M(x + m + n)) / D(x) + Cs * D(x + m + n) / D(x)


def test_hay_casos_suficientes():
    casos = list(casos_seguros())
    assert len(casos) > 300
    assert {c[3] for c in casos} == set(seguros.TIPOS)


@pytest.mark.parametrize("combo", COMBOS_SEGUROS, ids=IDS)
def test_distribucion(combo):
    """Probabilidades ≥ 0 que suman 1; valores estrictamente crecientes (agregados);
    media = prima por conmutación; componentes que suman la media."""
    fallos = []
    for c in casos_seguros([combo]):
        D = seguros.calcular(*c, ordenes=(1, 2))
        probs = [r["prob"] for r in D["rows"]]
        vals = [r["val"] for r in D["rows"]]
        va = prima_conmutacion(c)
        media = D["metricas"]["media"]
        if min(probs) < -TOL_ID:
            fallos.append(("prob < 0", c))
        if abs(sum(probs) - 1) > 1e-12 or abs(D["prob_total"] - 1) > 1e-12:
            fallos.append(("Σ prob ≠ 1", c, sum(probs)))
        if any(b <= a for a, b in zip(vals, vals[1:])):
            fallos.append(("valores no crecientes o repetidos", c))
        if abs(media - va) > 1e-12 * max(1.0, va):
            fallos.append(("media ≠ conmutación", c, media, va))
        comp = D["componentes"]
        if abs(comp["fallecimiento"] + comp["supervivencia"] - media) > 1e-12 * max(1.0, media):
            fallos.append(("componentes", c))
    assert not fallos, fallos[:5]


@pytest.mark.parametrize("combo", COMBOS_SEGUROS, ids=IDS)
def test_metricas(combo):
    fallos = []
    for c in casos_seguros([combo]):
        D = seguros.calcular(*c, ordenes=(1, 2, 3, 4))
        M, mom, rows = D["metricas"], D["momentos"], D["rows"]
        cs = [M["cuantiles"][a] for a in distribucion.PCTS]
        vmax = max(r["val"] for r in rows if r["prob"] > 0)
        ok = (M["var"] >= 0
              and abs(M["sd"] ** 2 - M["var"]) <= 1e-9 * max(1.0, M["var"])
              and abs(M["var"] - (mom[2] - mom[1] ** 2)) <= 1e-9 * max(1.0, mom[2])
              and all(b >= a for a, b in zip(cs, cs[1:]))
              and M["var995"] == M["cuantiles"][0.995]
              and M["var995"] - 1e-9 <= M["tvar995"] <= vmax + 1e-9)
        if not ok:
            fallos.append(c)
    assert not fallos, fallos[:5]


@pytest.mark.parametrize("combo", COMBOS_SEGUROS, ids=IDS)
def test_relacion_con_rentas(combo):
    """Aₓ = 1 − d·äₓ  y  Aₓ:ₙ⌉ = 1 − d·äₓ:ₙ⌉  (d = 1 − v), contra la pestaña de rentas."""
    key, sex = combo
    fallos = []
    for x in (0, 30, 65, 100, 108):
        if seguros.validar_tabla(key, sex, 2026, x):
            continue
        for I in (0.0, 0.0195, 0.05):
            d = 1 - 1 / (1 + I)
            A = seguros.calcular(key, sex, 2026, "vida_entera", x, 0, 0, I, 1.0, 0.0)["metricas"]["media"]
            a = rentas.calcular(key, sex, 2026, x, 1, 1, 0, I, 1.0, True, True)["metricas"]["media"]
            if abs(A - (1 - d * a)) > 1e-12:
                fallos.append(("vida entera", x, I, A, 1 - d * a))
            for n in (1, 10, 35):
                Am = seguros.calcular(key, sex, 2026, "mixto", x, n, 0, I, 1.0, 1.0)["metricas"]["media"]
                an = rentas.calcular(key, sex, 2026, x, n, 1, 0, I, 1.0, True, False)["metricas"]["media"]
                if abs(Am - (1 - d * an)) > 1e-12:
                    fallos.append(("mixto", x, n, I, Am, 1 - d * an))
    assert not fallos, fallos[:5]


@pytest.mark.parametrize("combo", COMBOS_SEGUROS, ids=IDS)
def test_descomposiciones(combo):
    """Aₓ = A¹ₓ:ₙ⌉ + ₙ|Aₓ;  Aₓ:ₙ⌉ = A¹ₓ:ₙ⌉ + ₙEₓ;  ₘ|Aₓ:ₙ⌉ = ₘ|A¹ₓ:ₙ⌉ + ₘ₊ₙEₓ;
    E[Z²] con capital 1 = E[Z] al tipo (1 + I)² − 1."""
    key, sex = combo
    S = lambda *a: seguros.calcular(key, sex, 2026, *a, ordenes=(1, 2))  # noqa: E731
    fallos = []
    for x in (0, 40, 65, 100):
        if seguros.validar_tabla(key, sex, 2026, x):
            continue
        for I in (0.0195, 0.05):
            I2 = (1 + I) ** 2 - 1
            for n in (1, 10, 35):
                if x + n >= 121:
                    continue
                Ax = S("vida_entera", x, 0, 0, I, 1.0, 0.0)["metricas"]["media"]
                A1 = S("temporal", x, n, 0, I, 1.0, 0.0)["metricas"]["media"]
                nAx = S("vida_entera", x, 0, n, I, 1.0, 0.0)["metricas"]["media"]
                nEx = S("capital_diferido", x, n, 0, I, 0.0, 1.0)["metricas"]["media"]
                Axn = S("mixto", x, n, 0, I, 1.0, 1.0)["metricas"]["media"]
                if abs(Ax - (A1 + nAx)) > 1e-12 or abs(Axn - (A1 + nEx)) > 1e-12:
                    fallos.append(("descomposición", x, n, I))
                for m in (3, 20):
                    mix = S("mixto", x, n, m, I, 1.0, 1.0)["metricas"]["media"]
                    mA1 = S("temporal", x, n, m, I, 1.0, 0.0)["metricas"]["media"]
                    E = S("capital_diferido", x, m + n, 0, I, 0.0, 1.0)["metricas"]["media"]
                    if abs(mix - (mA1 + E)) > 1e-12:
                        fallos.append(("mixto diferido", x, n, m, I))
                for tipo in seguros.TIPOS:
                    D = S(tipo, x, n, 3 if tipo != "capital_diferido" else 0, I, 1.0, 1.0)
                    D2 = S(tipo, x, n, 3 if tipo != "capital_diferido" else 0, I2, 1.0, 1.0)
                    if abs(D["momentos"][2] - D2["metricas"]["media"]) > 1e-12:
                        fallos.append(("²A", tipo, x, n, I))
    assert not fallos, fallos[:5]


def test_mixto_como_en_los_apuntes():
    """C_f = C_s y m = 0: el último valor C·vⁿ lleva ₙ₋₁|qₓ + ₙpₓ = ₙ₋₁pₓ."""
    key, sex, x, n, I = "pasem_gen_2", "M", 40, 10, 0.02
    D = seguros.calcular(key, sex, 2026, "mixto", x, n, 0, I, 1000.0, 1000.0)
    assert len(D["rows"]) == n
    r = D["rows"][0]  # el menor valor: C·vⁿ
    l = _l(key, sex, 2026, x)
    assert abs(r["val"] - 1000 * 1.02 ** -n) < 1e-12
    assert abs(r["prob"] - l[x + n - 1] / l[x]) < 1e-15
    assert sorted(e["cap"] for e in r["eventos"]) == ["f", "s"]


def test_casos_triviales():
    # I = 0 en el vida entera: Z = C con certeza
    D = seguros.calcular("per_ind_2", "H", 2026, "vida_entera", 50, 0, 0, 0.0, 300.0, 0.0)
    assert len(D["rows"]) == 1 and abs(D["rows"][0]["val"] - 300) < 1e-12 and abs(D["rows"][0]["prob"] - 1) < 1e-12
    # temporal a 1 año: C·v con qₓ, 0 con pₓ
    D = seguros.calcular("pasem_gen_2", "H", 2026, "temporal", 30, 1, 0, 0.03, 1.0, 0.0)
    q = tablas.compute("pasem_gen_2", "H", 30, 1, 0, 2026)["nqx"]
    assert abs(D["metricas"]["media"] - q / 1.03) < 1e-15


def test_prima_recargada():
    for alpha in (0.0, 0.05, 0.3):
        D = seguros.calcular("per_col_2", "M", 2026, "mixto", 45, 20, 0, 0.0195, 1e5, 5e4, alpha=alpha)
        P = D["prima"]
        assert P["pura"] == D["metricas"]["media"] and abs(P["recargo"] - alpha * P["pura"]) < 1e-9
        assert abs(P["recargada"] - (P["pura"] + P["recargo"])) < 1e-9
        R = rentas.calcular("per_col_2", "M", 2026, 65, 20, 12, 0, 0.0195, 100.0, True, False, alpha=alpha)["prima"]
        assert abs(R["recargada"] - (1 + alpha) * R["pura"]) < 1e-9
    assert distribucion.validar_recargo(-0.01) and distribucion.validar_recargo(float("nan"))
    assert distribucion.validar_recargo(0.0) is None


def test_lx_nula_es_error():
    assert "lₓ = 0" in seguros.validar_tabla("pasem_gen_2", "M", 2026, 111)
    with pytest.raises(ValueError):
        seguros.calcular("pasem_gen_2", "M", 2026, "temporal", 111, 1, 0, 0.02, 1.0, 0.0)


@pytest.mark.parametrize("args,trozo", [
    (("otro", 30, 10, 0, 0.02, 1, 1), "desconocido"),
    (("temporal", 30.5, 10, 0, 0.02, 1, 1), "edad x"),
    (("temporal", 121, 10, 0, 0.02, 1, 1), "edad x"),
    (("temporal", 30, 0, 0, 0.02, 1, 1), "duración n"),
    (("mixto", 30, 2.5, 0, 0.02, 1, 1), "duración n"),
    (("temporal", 30, 10, 1.5, 0.02, 1, 1), "diferimiento m"),
    (("vida_entera", 100, 0, 21, 0.02, 1, 1), "edad máxima"),
    (("temporal", 30, 10, 0, -1, 1, 1), "tipo de interés"),
    (("temporal", 30, 10, 0, 0.02, 0, 1), "fallecimiento"),
    (("capital_diferido", 30, 10, 0, 0.02, 1, 0), "supervivencia"),
    (("mixto", 30, 10, 0, 0.02, 1, -5), "supervivencia"),
])
def test_validacion(args, trozo):
    assert trozo in seguros.validar(*args)


def test_validacion_sin_error():
    assert seguros.validar("capital_diferido", 30, 10, 7.5, 0.02, 0, 1) is None   # m no interviene
    assert seguros.validar("vida_entera", 30, 0.5, 0, 0.02, 1, 0) is None         # n no interviene
    assert "año" in seguros.validar("temporal", 30, 10, 0, 0.02, 1, 1, need_year=True, year=1800)

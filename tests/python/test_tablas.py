"""Tablas de mortalidad: construcción de l_x, identidades y esperanzas de vida."""
import itertools
import math

import pytest

import tablas
from casos import TABLAS, SEXOS, METODOS, AÑOS, TOL_ID, casos_tablas
from datos import TABLES

GRUPOS = [(k, s, m) for k, s, m in itertools.product(TABLAS, SEXOS, METODOS)]
IDS = [f"{k}-{s}-{m}" for k, s, m in GRUPOS]


def vectores(key, sex):
    años = AÑOS if tablas.is_per(key) else (2026,)
    for año in años:
        for x in (0, 40, 65, 90):
            q = tablas.mortality_vector(key, sex, año - x)
            yield año, x, q, tablas.build_lx(q)


@pytest.mark.parametrize("key", TABLAS)
@pytest.mark.parametrize("sex", SEXOS)
def test_vector_q_y_lx(key, sex):
    for año, x, q, l in vectores(key, sex):
        assert len(q) == 121 and len(l) == 122
        assert all(0.0 <= v <= 1.0 for v in q)
        assert q[120] == 1.0, "ω = 121 exige q_120 = 1"
        assert l[0] == tablas.RADIX and l[121] == 0.0
        assert all(l[y + 1] <= l[y] for y in range(121)), "l_x debe ser no creciente"
        # l_{y+1} = l_y (1 − q_y)
        assert all(abs(l[y + 1] - l[y] * (1 - q[y])) <= 1e-9 for y in range(121))


@pytest.mark.parametrize("key,sex,met", GRUPOS, ids=IDS)
def test_identidad_de_control(key, sex, met):
    """_m q_x + _{m|n} q_x + _{m+n} p_x = 1 y _n p_x + _n q_x = 1."""
    fallos = []
    for k, s, año, mt, x, n, m in casos_tablas():
        if (k, s, mt) != (key, sex, met):
            continue
        r = tablas.compute(key, sex, x, n, m, año, met)
        if r["lx"] <= 0:
            continue
        suma = r["mqx"] + r["mnqx"] + r["mnpx"]
        if abs(suma - 1) > TOL_ID or abs(r["npx"] + r["nqx"] - 1) > TOL_ID:
            fallos.append((año, x, n, m, suma))
        for v in ("npx", "nqx", "mnqx", "mqx", "mnpx"):
            if not -TOL_ID <= r[v] <= 1 + TOL_ID:
                fallos.append((año, x, n, m, v, r[v]))
    assert not fallos, fallos[:5]


@pytest.mark.parametrize("key,sex,met", GRUPOS, ids=IDS)
def test_l_interpolada(key, sex, met):
    """En edades enteras l_at devuelve l_y; entre ellas, valores intermedios coherentes con el método."""
    for año, x, q, l in vectores(key, sex):
        for y in range(120):
            assert tablas.l_at(l, y, met) == l[y]
            for s in (0.25, 0.5, 0.9):
                v = tablas.l_at(l, y + s, met)
                assert l[y + 1] - 1e-9 <= v <= l[y] + 1e-9
                esperado = 1 - s * q[y] if met == "lin" else (1 - q[y]) ** s  # _s p_y
                if l[y] > 0:
                    assert abs(v / l[y] - esperado) < 1e-12
        assert tablas.l_at(l, 121, met) == 0.0 and tablas.l_at(l, -1, met) == 0.0


@pytest.mark.parametrize("key,sex,met", GRUPOS, ids=IDS)
def test_mu_coherente_con_l(key, sex, met):
    """μ_a = −d ln l_a / da (derivada numérica centrada, dentro de cada año)."""
    año, x, q, l = next(vectores(key, sex))
    h = 1e-6
    for y in range(0, 119):
        if q[y] >= 1:
            continue
        for s in (0.2, 0.5, 0.8):
            a = y + s
            num = -(math.log(tablas.l_at(l, a + h, met)) - math.log(tablas.l_at(l, a - h, met))) / (2 * h)
            mu = tablas.mu_at(q, a, met)
            assert mu is not None
            assert abs(mu - num) <= 1e-5 * max(1.0, mu), (y, s, mu, num)


@pytest.mark.parametrize("key,sex", list(itertools.product(TABLAS, SEXOS)))
def test_esperanza_completa_udd(key, sex):
    """Con UDD y x entera, e̊_x = e_x + ½ exactamente (l lineal en cada año y l_121 = 0)."""
    for año in (AÑOS if tablas.is_per(key) else (2026,)):
        for x in range(0, 121, 5):
            r = tablas.compute(key, sex, x, 1, 0, año, "lin")
            if r["lx"] > 0:
                assert abs(r["ecx"] - (r["ex"] + 0.5)) < 1e-9, (año, x, r["ecx"], r["ex"])


@pytest.mark.parametrize("key", TABLAS)
def test_lx_nula_no_da_resultado(key):
    """Si nadie llega a la edad x (l_x = 0), las probabilidades no están definidas (NaN)."""
    x = next(x for x in range(121) if tablas.compute(key, "M", x, 1, 0, 2026)["lx"] <= 0)
    r = tablas.compute(key, "M", x, 1, 0, 2026)
    assert all(math.isnan(r[v]) for v in ("npx", "nqx", "mnqx", "mqx", "mnpx", "ex"))


@pytest.mark.parametrize("key,sex,met", GRUPOS, ids=IDS)
def test_esperanza_completa_integral(key, sex, met):
    """e̊_x coincide con ∫ l_{x+t}/l_x dt calculada numéricamente (Simpson, paso 1/200)."""
    año, _, q, l = next(vectores(key, sex))
    for x in (0, 30.4, 65, 99.5):
        lx = tablas.l_at(l, x, met)
        N = int(round((tablas.OMEGA - x) * 200))
        N += N % 2
        h = (tablas.OMEGA - x) / N
        f = [tablas.l_at(l, x + i * h, met) / lx for i in range(N + 1)]
        simpson = h / 3 * (f[0] + f[-1] + 4 * sum(f[1:-1:2]) + 2 * sum(f[2:-1:2]))
        assert abs(tablas.e_complete(l, x, met) - simpson) < 1e-4, (x, simpson)


def test_generacional_mejora_con_el_año():
    """PER2020: con λ ≥ 0, una cohorte más reciente no tiene mayor mortalidad a ninguna edad."""
    for key in [k for k in TABLAS if tablas.is_per(k)]:
        for sex in SEXOS:
            assert all(v >= 0 for v in TABLES[key]["data"][sex]["lam"])
            q1 = tablas.mortality_vector(key, sex, 1950)
            q2 = tablas.mortality_vector(key, sex, 2000)
            assert all(b <= a + 1e-15 for a, b in zip(q1, q2))


def test_estaticas_no_dependen_del_año():
    for key in [k for k in TABLAS if not tablas.is_per(k)]:
        for sex in SEXOS:
            a = tablas.compute(key, sex, 50, 10, 5, 1960)
            b = tablas.compute(key, sex, 50, 10, 5, 2100)
            assert a["npx"] == b["npx"] and a["mnqx"] == b["mnqx"]

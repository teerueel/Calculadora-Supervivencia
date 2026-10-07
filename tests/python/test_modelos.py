"""Modelos paramétricos: S(x), μ coherente con H, identidades y esperanza completa."""
import itertools
import math

import pytest

import modelos
from casos import MODELOS, SEXOS, METODOS, EDADES, PLAZOS, DIFERIMIENTOS, TOL_ID

CONTINUOS = [k for k in MODELOS if modelos.MODELS[k]["kind"] == "cont"]
GRUPOS = list(itertools.product(MODELOS, SEXOS))
IDS = [f"{k}-{s}" for k, s in GRUPOS]


def evaluador(key, sex, met="lin"):
    return modelos.Evaluator(key, modelos.default_params(key, sex), met)


def test_hay_presets_para_todos():
    for key, sex in GRUPOS:
        p = modelos.default_params(key, sex)
        assert set(p) == {d["k"] for d in modelos.MODELS[key]["params"]}


@pytest.mark.parametrize("key,sex", GRUPOS, ids=IDS)
def test_supervivencia(key, sex):
    """S(0) = 1 y S no creciente."""
    E = evaluador(key, sex)
    assert abs(E.S(0) - 1) < TOL_ID
    vals = [E.S(a / 4) for a in range(0, 4 * 121 + 1)]
    assert all(0 <= v <= 1 + TOL_ID for v in vals)
    assert all(b <= a + TOL_ID for a, b in zip(vals, vals[1:]))


@pytest.mark.parametrize("key,sex", GRUPOS, ids=IDS)
@pytest.mark.parametrize("met", METODOS)
def test_identidad_de_control(key, sex, met):
    E = evaluador(key, sex, met)
    fallos = []
    for x, n, m in itertools.product(EDADES, PLAZOS, DIFERIMIENTOS):
        r = E.compute(x, n, m)
        if r["lx"] <= 0:
            continue
        suma = r["mqx"] + r["mnqx"] + r["mnpx"]
        if abs(suma - 1) > TOL_ID or abs(r["npx"] + r["nqx"] - 1) > TOL_ID:
            fallos.append((x, n, m, suma))
    assert not fallos, fallos[:5]


@pytest.mark.parametrize("key", CONTINUOS)
@pytest.mark.parametrize("sex", SEXOS)
def test_mu_es_derivada_de_H(key, sex):
    """μ(x) = H'(x): comprueba que las fórmulas de μ y de H de cada modelo son coherentes."""
    M, p = modelos.MODELS[key], modelos.default_params(key, sex)
    h = 1e-5
    for a in [0.5] + list(range(1, 111)):
        if key == "demoivre" and a + h >= p["w"]:
            break
        num = (M["H"](a + h, p) - M["H"](a - h, p)) / (2 * h)
        mu = M["mu"](a, p)
        assert abs(mu - num) <= 1e-6 * max(1.0, mu), (a, mu, num)


@pytest.mark.parametrize("key", CONTINUOS)
@pytest.mark.parametrize("sex", SEXOS)
def test_esperanza_completa(key, sex):
    """e̊_x frente a ∫_0^∞ S(x+t)/S(x) dt por Simpson con paso fino (incluye las formas cerradas)."""
    E = evaluador(key, sex)
    for x in (0, 40, 65.5, 90):
        sx = E.S(x)
        if sx <= 0:
            continue
        h, simpson, t = 0.01, 0.0, 0.0   # por tramos de 10 años hasta que la cola sea < 1e-13
        while True:
            f = [E.S(x + t + i * h) / sx for i in range(1001)]
            simpson += h / 3 * (f[0] + f[-1] + 4 * sum(f[1:-1:2]) + 2 * sum(f[2:-1:2]))
            t += 10
            if f[-1] < 1e-13 or t > 20000:
                break
        assert abs(E.e_complete(x) - simpson) < 1e-6 * max(1.0, simpson), (x, E.e_complete(x), simpson)


@pytest.mark.parametrize("sex", SEXOS)
def test_heligman_pollard_como_tabla(sex):
    E = evaluador("heligman_pollard", sex)
    assert all(0 <= q <= 1 for q in E.q) and E.q[120] == 1.0
    assert all(E.l[y + 1] <= E.l[y] for y in range(121))
    # q/p = A^((x+B)^C) + D e^(−E (ln x − ln F)²) + G Hˣ
    p = modelos.default_params("heligman_pollard", sex)
    for x in (1, 20, 60, 100):
        q = E.q[x]
        r = p["A"] ** ((x + p["B"]) ** p["C"]) + p["D"] * math.exp(-p["E"] * math.log(x / p["F"]) ** 2) + p["G"] * p["H"] ** x
        assert abs(q / (1 - q) - r) < 1e-12 * max(1.0, r)

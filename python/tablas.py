"""
Motor de cálculo con tablas de mortalidad.

Convenciones del proyecto (CLAUDE.md, §3):
  · todo se calcula a partir de l_x:  l_0 = 100 000,  l_{y+1} = l_y (1 − q_y),  ω = 121;
  · PER2020 (generacional): q_{y, C+y} = q_{y,2012} · e^{−λ_y (C + y − 2012)}, C = año − x;
  · PASEM2020 (estática): q tal cual, año base 2019;
  · q publicadas en tanto por mil, acotadas a [0, 1].

Edades no enteras: l se interpola entre edades enteras consecutivas.
  · lineal (UDD):             l_{y+s} = l_y − s (l_y − l_{y+1})   ⇒  _s p_y = 1 − s q_y
  · exponencial (μ constante): l_{y+s} = l_y · p_y^s               ⇒  _s p_y = p_y^s
No se inventan q_x: solo se reparte dentro del año la mortalidad publicada.
"""
import math

from datos import TABLES

OMEGA = 121
RADIX = 100_000.0
INTERP = {"lin": "Lineal (UDD)", "exp": "Exponencial (fuerza constante)"}


def is_per(key):
    return TABLES[key]["kind"] == "per"


def mortality_vector(key, sex, cohort):
    """q_y, y = 0..120, siguiendo la diagonal de la cohorte en tablas generacionales."""
    t = TABLES[key]
    q = []
    for y in range(121):
        if t["kind"] == "per":
            d = t["data"][sex]
            v = d["qb"][y] / 1000 * math.exp(-d["lam"][y] * (cohort + y - t["base"]))
        else:
            v = t["data"][sex][y] / 1000
        q.append(min(1.0, max(0.0, v)))
    q[120] = 1.0
    return q


def build_lx(q, radix=RADIX):
    """l tiene 122 posiciones (0..121); l_121 = 0."""
    l = [radix]
    for y in range(121):
        l.append(l[y] * (1 - q[y]))
    return l


def l_at(l, a, metodo="lin"):
    """l en una edad real a ≥ 0 con la interpolación elegida. Fuera de rango → 0."""
    if a < 0 or a >= OMEGA:
        return 0.0
    y = int(math.floor(a + 1e-12))
    s = a - y
    if s < 1e-12:
        return l[y]
    ly, ly1 = l[y], l[y + 1]
    if metodo == "lin":
        return ly - s * (ly - ly1)
    if ly <= 0:
        return 0.0
    return ly * (ly1 / ly) ** s


def mu_at(q, a, metodo="lin"):
    """Tanto instantáneo μ en la edad a según la hipótesis de fraccionamiento."""
    if a < 0 or a >= OMEGA - 1:  # en [120, 121) q = 1 y μ diverge
        return None
    y = int(math.floor(a + 1e-12))
    s = a - y
    qy = q[y]
    if metodo == "lin":
        return qy / (1 - s * qy) if s * qy < 1 else None
    return -math.log(1 - qy) if qy < 1 else None


def _seg_integral(ly, ly1, s0, metodo):
    """∫_{s0}^{1} l_{y+s} ds."""
    if metodo == "lin":
        d = ly - ly1
        return ly * (1 - s0) - d * (1 - s0 * s0) / 2
    if ly <= 0:
        return 0.0
    p = ly1 / ly
    if p <= 0:
        return 0.0
    if abs(p - 1) < 1e-15:
        return ly * (1 - s0)
    return ly * (p - p ** s0) / math.log(p)


def e_complete(l, x, metodo):
    """ e̊_x = (1/l_x) ∫_x^ω l_a da, con l interpolada."""
    lx = l_at(l, x, metodo)
    if lx <= 0:
        return 0.0
    y = int(math.floor(x + 1e-12))
    tot = _seg_integral(l[y], l[y + 1], x - y, metodo)
    for k in range(y + 1, OMEGA):
        tot += _seg_integral(l[k], l[k + 1], 0.0, metodo)
    return tot / lx


def compute(key, sex, x, n, m, year, metodo="lin"):
    """Resultados principales. x, n, m pueden ser reales (se usa la interpolación)."""
    cohort = (year - math.floor(x)) if is_per(key) else None
    q = mortality_vector(key, sex, cohort if cohort is not None else 0)
    l = build_lx(q)
    L = lambda a: l_at(l, a, metodo)  # noqa: E731
    lx, lxn, lxm, lxmn = L(x), L(x + n), L(x + m), L(x + m + n)
    nan = float("nan")
    ok = lx > 0  # si l_x = 0 nadie llega a la edad x: las probabilidades no están definidas
    npx = lxn / lx if ok else nan
    res = dict(q=q, l=l, cohort=cohort, lx=lx, lxn=lxn, lxm=lxm, lxmn=lxmn,
               npx=npx, nqx=1 - npx,
               mnqx=(lxm - lxmn) / lx if ok else nan, mqx=1 - lxm / lx if ok else nan, mnpx=lxmn / lx if ok else nan)
    # e_x abreviada (edad entera): Σ_{k≥1} l_{x+k}/l_x ; e̊_x con la interpolación elegida
    res["ex"] = sum(L(x + k) for k in range(1, OMEGA + 1) if x + k < OMEGA) / lx if ok else nan
    res["ecx"] = e_complete(l, x, metodo)
    return res


def tpx_frac(l, x, t, metodo):
    """_t p_x con x y t reales: l_{x+t} / l_x."""
    a, b = l_at(l, x + t, metodo), l_at(l, x, metodo)
    return (a / b if b > 0 else float("nan")), a, b


def curves(res, x, metodo, step=0.25):
    """Rejilla en t para _t p_x, _t q_x y μ_{x+t}."""
    l, q = res["l"], res["q"]
    lx = l_at(l, x, metodo)
    ts, S, F, MU = [], [], [], []
    t = 0.0
    while x + t <= OMEGA + 1e-9:
        p = l_at(l, x + t, metodo) / lx if lx > 0 else float("nan")
        ts.append(t)
        S.append(p)
        F.append(1 - p)
        MU.append(mu_at(q, x + t, metodo))
        t = round(t + step, 10)
    return ts, S, F, MU

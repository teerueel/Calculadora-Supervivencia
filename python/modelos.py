"""
Modelos paramétricos de supervivencia.

Cada modelo continuo define el tanto instantáneo μ(x) y su integral
H(x) = ∫_0^x μ(s) ds, de modo que S(x) = e^{−H(x)} hace de l_x / l_0 y

    _t p_x = S(x+t) / S(x)        (misma lógica que con l_x en las tablas).

Heligman–Pollard se formula sobre q_x (discreto): se construye l_x en edades
enteras (ω = 121) y las edades no enteras se tratan con la interpolación elegida,
exactamente igual que con una tabla.

Los valores iniciales de los parámetros (PRESETS) NO son valores publicados:
se han obtenido ajustando cada modelo a la PASEM2020 General 2º orden de cada
sexo por mínimos cuadrados (ver ajuste_presets.py, que permite reproducirlos).
"""
import math

import tablas

OMEGA = 121


def _phi(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _log1p_safe(v):
    return math.log1p(v) if v > -1 else float("-inf")


# ------------------------------------------------------------------ definiciones
# Parámetro: (clave, símbolo, mínimo, máximo, escala, descripción)
def P(k, sym, lo, hi, scale, desc):
    return dict(k=k, sym=sym, min=lo, max=hi, scale=scale, desc=desc)


MODELS = {
    "exponencial": dict(
        name="Exponencial", family="Clásicos", kind="cont",
        formula="μₓ = λ",
        params=[P("lam", "λ", 1e-4, 0.5, "log", "fuerza de mortalidad constante")],
        mu=lambda x, p: p["lam"],
        H=lambda x, p: p["lam"] * x),
    "demoivre": dict(
        name="De Moivre", family="Clásicos", kind="cont",
        formula="μₓ = 1 / (ω − x)",
        params=[P("w", "ω", 50, 160, "lin", "edad límite")],
        mu=lambda x, p: 1 / (p["w"] - x) if x < p["w"] else math.inf,
        H=lambda x, p: -math.log(1 - x / p["w"]) if x < p["w"] else math.inf),
    "gompertz": dict(
        name="Gompertz", family="Clásicos", kind="cont",
        formula="μₓ = B·cˣ",
        params=[P("B", "B", 1e-7, 1e-3, "log", "nivel de la mortalidad"),
                P("c", "c", 1.01, 1.2, "lin", "ritmo de envejecimiento")],
        mu=lambda x, p: p["B"] * p["c"] ** x,
        H=lambda x, p: p["B"] / math.log(p["c"]) * (p["c"] ** x - 1)),
    "makeham": dict(
        name="Makeham", family="Clásicos", kind="cont",
        formula="μₓ = A + B·cˣ",
        params=[P("A", "A", 0, 5e-3, "lin", "mortalidad independiente de la edad"),
                P("B", "B", 1e-7, 1e-3, "log", "nivel de la senescencia"),
                P("c", "c", 1.01, 1.2, "lin", "ritmo de envejecimiento")],
        mu=lambda x, p: p["A"] + p["B"] * p["c"] ** x,
        H=lambda x, p: p["A"] * x + p["B"] / math.log(p["c"]) * (p["c"] ** x - 1)),
    "weibull": dict(
        name="Weibull", family="Clásicos", kind="cont",
        formula="μₓ = (β/θ)·(x/θ)^(β−1)",
        params=[P("be", "β", 0.3, 15, "lin", "forma"),
                P("th", "θ", 20, 120, "lin", "escala (edad característica)")],
        mu=lambda x, p: (p["be"] / p["th"]) * (x / p["th"]) ** (p["be"] - 1) if x > 0 or p["be"] >= 1 else math.inf,
        H=lambda x, p: (x / p["th"]) ** p["be"]),
    "perks": dict(
        name="Perks", family="Logísticos", kind="cont",
        formula="μₓ = (A + B·cˣ) / (1 + D·cˣ)",
        params=[P("A", "A", 0, 5e-3, "lin", "mortalidad independiente de la edad"),
                P("B", "B", 1e-7, 1e-3, "log", "nivel de la senescencia"),
                P("c", "c", 1.01, 1.2, "lin", "ritmo de envejecimiento"),
                P("D", "D", 1e-7, 1e-3, "log", "freno logístico")],
        mu=lambda x, p: (p["A"] + p["B"] * p["c"] ** x) / (1 + p["D"] * p["c"] ** x),
        H=lambda x, p: p["A"] * x + (p["B"] - p["A"] * p["D"]) / (p["D"] * math.log(p["c"]))
        * (math.log1p(p["D"] * p["c"] ** x) - math.log1p(p["D"]))),
    "kannisto": dict(
        name="Kannisto", family="Logísticos", kind="cont",
        formula="μₓ = a·e^(bx) / (1 + a·e^(bx))",
        params=[P("a", "a", 1e-9, 1e-2, "log", "nivel"),
                P("b", "b", 0.03, 0.2, "lin", "ritmo de crecimiento")],
        mu=lambda x, p: (lambda r: r / (1 + r))(p["a"] * math.exp(p["b"] * x)),
        H=lambda x, p: (math.log1p(p["a"] * math.exp(p["b"] * x)) - math.log1p(p["a"])) / p["b"]),
    "thiele": dict(
        name="Thiele", family="Curva completa", kind="cont",
        formula="μₓ = a₁e^(−b₁x) + a₂e^(−½b₂(x−c)²) + a₃e^(b₃x)",
        params=[P("a1", "a₁", 1e-4, 0.2, "log", "nivel infantil"),
                P("b1", "b₁", 0.05, 5, "lin", "descenso infantil"),
                P("a2", "a₂", 1e-6, 1e-2, "log", "intensidad de la joroba"),
                P("b2", "b₂", 1e-4, 0.2, "log", "concentración de la joroba"),
                P("c", "c", 10, 40, "lin", "edad de la joroba"),
                P("a3", "a₃", 1e-7, 1e-3, "log", "nivel de la senescencia"),
                P("b3", "b₃", 0.05, 0.2, "lin", "ritmo de envejecimiento")],
        mu=lambda x, p: p["a1"] * math.exp(-p["b1"] * x)
        + p["a2"] * math.exp(-0.5 * p["b2"] * (x - p["c"]) ** 2) + p["a3"] * math.exp(p["b3"] * x),
        H=lambda x, p: p["a1"] / p["b1"] * (1 - math.exp(-p["b1"] * x))
        + p["a2"] * math.sqrt(2 * math.pi / p["b2"])
        * (_phi(math.sqrt(p["b2"]) * (x - p["c"])) - _phi(-math.sqrt(p["b2"]) * p["c"]))
        + p["a3"] / p["b3"] * (math.exp(p["b3"] * x) - 1)),
    "siler": dict(
        name="Siler", family="Curva completa", kind="cont",
        formula="μₓ = a₁e^(−b₁x) + a₂ + a₃e^(b₃x)",
        params=[P("a1", "a₁", 1e-4, 0.2, "log", "nivel infantil"),
                P("b1", "b₁", 0.05, 5, "lin", "descenso infantil"),
                P("a2", "a₂", 0, 5e-3, "lin", "mortalidad de fondo"),
                P("a3", "a₃", 1e-7, 1e-3, "log", "nivel de la senescencia"),
                P("b3", "b₃", 0.05, 0.2, "lin", "ritmo de envejecimiento")],
        mu=lambda x, p: p["a1"] * math.exp(-p["b1"] * x) + p["a2"] + p["a3"] * math.exp(p["b3"] * x),
        H=lambda x, p: p["a1"] / p["b1"] * (1 - math.exp(-p["b1"] * x)) + p["a2"] * x
        + p["a3"] / p["b3"] * (math.exp(p["b3"] * x) - 1)),
    "heligman_pollard": dict(
        name="Heligman–Pollard", family="Curva completa", kind="disc",
        formula="qₓ/pₓ = A^((x+B)^C) + D·e^(−E(ln x − ln F)²) + G·Hˣ",
        params=[P("A", "A", 1e-5, 0.05, "log", "nivel de la mortalidad infantil"),
                P("B", "B", 1e-5, 0.5, "log", "desplazamiento de edad"),
                P("C", "C", 0.01, 0.5, "lin", "velocidad del descenso infantil"),
                P("D", "D", 1e-6, 1e-2, "log", "intensidad de la joroba"),
                P("E", "E", 0.5, 40, "lin", "dispersión de la joroba (inversa)"),
                P("F", "F", 10, 40, "lin", "edad de la joroba"),
                P("G", "G", 1e-7, 1e-3, "log", "nivel de la senescencia"),
                P("H", "H", 1.01, 1.2, "lin", "ritmo de envejecimiento")]),
}
MODEL_KEYS = list(MODELS)
MODEL_FAMILIES = ["Clásicos", "Logísticos", "Curva completa"]


def hp_q(x, p):
    r = p["A"] ** ((x + p["B"]) ** p["C"]) + p["G"] * p["H"] ** x
    if x > 0:
        r += p["D"] * math.exp(-p["E"] * (math.log(x) - math.log(p["F"])) ** 2)
    return r / (1 + r)


# ------------------------------------------------------------------ presets
# Ajustados a PASEM2020 General 2º orden (ver ajuste_presets.py).
PRESETS = {}  # se rellena al final del módulo (PRESETS_DATA)


def default_params(key, sex):
    return dict(PRESETS[key][sex])


# ------------------------------------------------------------------ evaluación
class Evaluator:
    """Encapsula un modelo con unos parámetros: S(a), μ(a), l_a y resultados."""

    def __init__(self, key, params, metodo="lin"):
        self.key, self.p, self.metodo = key, params, metodo
        self.m = MODELS[key]
        if self.m["kind"] == "disc":
            self.q = [min(1.0, max(0.0, hp_q(y, params))) for y in range(121)]
            self.q[120] = 1.0
            self.l = tablas.build_lx(self.q)

    def S(self, a):
        if self.m["kind"] == "disc":
            return tablas.l_at(self.l, a, self.metodo) / tablas.RADIX
        try:
            h = self.m["H"](a, self.p)
        except (OverflowError, ValueError, ZeroDivisionError):
            return 0.0
        return math.exp(-h) if math.isfinite(h) else 0.0

    def l_at(self, a):
        return tablas.RADIX * self.S(a)

    def mu(self, a):
        if self.m["kind"] == "disc":
            return tablas.mu_at(self.q, a, self.metodo)
        try:
            v = self.m["mu"](a, self.p)
        except (OverflowError, ValueError, ZeroDivisionError):
            return None
        return v if math.isfinite(v) else None

    def e_complete(self, x):
        """ e̊_x = ∫_0^∞ _t p_x dt (formas cerradas cuando existen; si no, Simpson)."""
        if self.key == "exponencial":
            return 1 / self.p["lam"]
        if self.key == "demoivre":
            return max(0.0, (self.p["w"] - x) / 2)
        if self.m["kind"] == "disc":
            return tablas.e_complete(self.l, x, self.metodo)
        sx = self.S(x)
        if sx <= 0:
            return 0.0
        h, tot, t = 0.05, 0.0, 0.0
        f0 = 1.0
        while t < 500:
            f1 = self.S(x + t + h) / sx
            f2 = self.S(x + t + 2 * h) / sx
            tot += h / 3 * (f0 + 4 * f1 + f2)
            t += 2 * h
            f0 = f2
            if f2 < 1e-12:
                break
        return tot

    def compute(self, x, n, m):
        L = self.l_at
        lx, lxn, lxm, lxmn = L(x), L(x + n), L(x + m), L(x + m + n)
        npx = lxn / lx if lx > 0 else float("nan")
        return dict(lx=lx, lxn=lxn, lxm=lxm, lxmn=lxmn, npx=npx, nqx=1 - npx,
                    mnqx=(lxm - lxmn) / lx if lx > 0 else float("nan"),
                    mqx=1 - lxm / lx if lx > 0 else float("nan"),
                    mnpx=lxmn / lx if lx > 0 else float("nan"),
                    ecx=self.e_complete(x))

    def curves(self, x, step=0.25):
        sx = self.S(x)
        ts, S, F, MU = [], [], [], []
        t = 0.0
        while x + t <= OMEGA + 1e-9:
            p = self.S(x + t) / sx if sx > 0 else float("nan")
            ts.append(t); S.append(p); F.append(1 - p); MU.append(self.mu(x + t))
            t = round(t + step, 10)
        return ts, S, F, MU


# Valores de partida por sexo (generados con ajuste_presets.py)
from presets_data import PRESETS_DATA  # noqa: E402

PRESETS.update(PRESETS_DATA)

"""
Reproduce los valores de partida (presets) de los modelos paramétricos.

Cada modelo se ajusta, para cada sexo, a la PASEM2020 General 2º orden
(estática, año base 2019) por mínimos cuadrados:

  · Exponencial: sobre la función de supervivencia S(x) = l_x / l_0, edades 0–100.
  · De Moivre: no se ajusta. Por mínimos cuadrados ω se va por encima de 160 años
    (síntoma de que la ley no reproduce la mortalidad humana), así que se toma la
    edad límite de las tablas del proyecto, ω = 121.
  · Resto: sobre ln q_x, en el tramo de edades para el que está pensado el modelo
    (Gompertz, Makeham, Weibull y Perks: 30–100; Kannisto: 80–100;
    Thiele, Siler y Heligman–Pollard: 0–100).

Se excluyen las edades > 100 porque el cierre de la tabla publicada no responde a
ninguna ley de mortalidad. Requiere scipy (solo para regenerar; la aplicación no lo usa).

Uso:  python ajuste_presets.py   → reescribe presets_data.py
"""
import math
import random

import numpy as np
from scipy.optimize import least_squares

import tablas
from modelos import MODELS, hp_q

RANGES = {"exponencial": (0, 100), "demoivre": (0, 100), "gompertz": (30, 100), "makeham": (30, 100),
          "weibull": (30, 100), "perks": (30, 100), "kannisto": (80, 100), "thiele": (0, 100),
          "siler": (0, 100), "heligman_pollard": (0, 100)}
ON_S = {"exponencial"}


def table_q(sex):
    q = tablas.mortality_vector("pasem_gen_2", sex, 0)
    return q, tablas.build_lx(q)


def model_q(key, p, x):
    m = MODELS[key]
    if m["kind"] == "disc":
        return hp_q(x, p)
    return 1 - math.exp(-(m["H"](x + 1, p) - m["H"](x, p)))


def fit(key, sex):
    m = MODELS[key]
    defs = m["params"]
    q, l = table_q(sex)
    a, b = RANGES[key]
    ages = range(a, b + 1)

    def to_p(z):
        return {d["k"]: (math.exp(v) if d["scale"] == "log" else v) for d, v in zip(defs, z)}

    lo = [math.log(d["min"]) if d["scale"] == "log" else d["min"] for d in defs]
    hi = [math.log(d["max"]) if d["scale"] == "log" else d["max"] for d in defs]

    def resid(z):
        p = to_p(z)
        out = []
        for x in ages:
            try:
                if key in ON_S:
                    s = math.exp(-m["H"](x, p)) if math.isfinite(m["H"](x, p)) else 0.0
                    out.append(s - l[x] / l[0])
                else:
                    qm = min(max(model_q(key, p, x), 1e-12), 1 - 1e-12)
                    out.append(math.log(qm) - math.log(q[x]))
            except (OverflowError, ValueError, ZeroDivisionError):
                out.append(1e3)
        return out

    rng = random.Random(1)
    best = None
    for _ in range(40):
        z0 = [rng.uniform(l_, h_) for l_, h_ in zip(lo, hi)]
        try:
            r = least_squares(resid, z0, bounds=(lo, hi), max_nfev=4000)
        except Exception:
            continue
        if best is None or r.cost < best.cost:
            best = r
    p = to_p(best.x)
    return {k: (0.0 if v < 1e-15 else float(f"{v:.6g}")) for k, v in p.items()}, best.cost


if __name__ == "__main__":
    res = {}
    for key in MODELS:
        res[key] = {}
        for sex in ("H", "M"):
            if key == "demoivre":
                p, cost = {"w": 121.0}, float("nan")
            else:
                p, cost = fit(key, sex)
            res[key][sex] = p
            print(f"{key:18s} {sex}  coste={cost:.4g}  {p}")
    with open("presets_data.py", "w", encoding="utf-8") as f:
        f.write('"""Valores de partida de los modelos paramétricos, generados con ajuste_presets.py.\n'
                'Ajuste por mínimos cuadrados a PASEM2020 General 2º orden (BOE-A-2020-17154)."""\n\n')
        f.write("PRESETS_DATA = {\n")
        for key, d in res.items():
            f.write(f"    {key!r}: {{\n")
            for sex, p in d.items():
                f.write(f"        {sex!r}: {p!r},\n")
            f.write("    },\n")
        f.write("}\n")

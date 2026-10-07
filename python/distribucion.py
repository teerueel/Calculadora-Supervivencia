"""
Variable aleatoria discreta del valor actual (rentas y seguros) y su prima.

Filas: listas de dicts con al menos 'val' (valor, en €) y 'prob'. Las funciones de cuantiles
exigen las filas ORDENADAS por valor creciente; agregar() las ordena y junta valores iguales.

  · E[Z^s] = Σ z^s · prob
  · Q(a) = mín { z : F(z) ≥ a }
  · TVaR_a = (1/(1−a)) ∫_a^1 Q(u) du   (válida con átomos)
  · Prima recargada con recargo de seguridad α ≥ 0 libre:  (1 + α) · E[Z]
"""
import math

PCTS = (0.05, 0.25, 0.50, 0.75, 0.95, 0.995)
ALPHA = 0.995  # nivel de Solvencia II


def agregar(eventos):
    """Ordena por valor y junta los valores iguales (|Δ| ≤ 1e-12·máx(1, |z|)).
    Cada fila resultante: val, prob y 'eventos' (lista de los eventos que la forman)."""
    out = []
    for e in sorted(eventos, key=lambda r: r["val"]):
        if out and abs(e["val"] - out[-1]["val"]) <= 1e-12 * max(1.0, abs(e["val"])):
            out[-1]["prob"] += e["prob"]
            out[-1]["eventos"].append(e)
        else:
            out.append(dict(val=e["val"], prob=e["prob"], eventos=[e]))
    return out


def momentos(rows, ordenes):
    """E[Z^s] = Σ valor^s · prob  para cada orden s pedido (en euros^s)."""
    return {s: sum(r["val"] ** s * r["prob"] for r in rows) for s in ordenes}


def cuantil(rows, a):
    """Q(a) = mín { z : F(z) ≥ a }  (distribución discreta, filas ordenadas)."""
    F = 0.0
    for r in rows:
        F += r["prob"]
        if F >= a - 1e-12:
            return r["val"]
    return rows[-1]["val"]


def tvar(rows, a):
    """TVaR_a = (1/(1−a)) ∫_a^1 Q(u) du  (válida también con átomos)."""
    F0, tot = 0.0, 0.0
    for r in rows:
        F1 = F0 + r["prob"]
        tot += r["val"] * max(0.0, F1 - max(F0, a))
        F0 = F1
    return tot / (1 - a)


def metricas(rows):
    """Momentos centrales calculados directamente, μ_k = Σ (z − E[Z])^k · prob (estable frente a la
    cancelación de E[Z²] − E[Z]²). σ por debajo del redondeo (≤ 1e-12·máx(1, |E[Z]|)) se toma 0:
    distribución degenerada, sin asimetría ni curtosis."""
    m1 = momentos(rows, (1,))[1]
    mu2, mu3, mu4 = (sum((r["val"] - m1) ** k * r["prob"] for r in rows) for k in (2, 3, 4))
    var = max(0.0, mu2)
    sd = math.sqrt(var)
    if sd <= 1e-12 * max(1.0, abs(m1)):
        var = sd = 0.0
    return dict(media=m1, var=var, sd=sd, cv=sd / m1 if m1 > 0 else float("nan"),
                asim=mu3 / sd ** 3 if sd > 0 else float("nan"),
                curt=mu4 / sd ** 4 if sd > 0 else float("nan"),
                cuantiles={a: cuantil(rows, a) for a in PCTS},
                var995=cuantil(rows, ALPHA), tvar995=tvar(rows, ALPHA))


def validar_recargo(alpha):
    if not math.isfinite(alpha) or alpha < 0:
        return "El recargo de seguridad α debe ser un porcentaje mayor o igual que 0."
    return None


def prima(pura, alpha):
    """Prima pura, importe del recargo α·E[Z] y prima recargada (1 + α)·E[Z]."""
    return dict(alpha=alpha, pura=pura, recargo=alpha * pura, recargada=(1 + alpha) * pura)

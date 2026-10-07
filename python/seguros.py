"""
Seguros de vida sobre una cabeza (capa de producto): distribución del valor actual Z, momentos,
prima pura única, prima recargada y métricas de riesgo.

Hipótesis: x, n y m enteros; el capital de fallecimiento se paga al FINAL del año de
fallecimiento; v(t) = (1 + I)^(−t) (capa de descuento); w = 120. Probabilidades leídas de lₓ:
  _{t|}qₓ = (l_{x+t} − l_{x+t+1}) / lₓ,   ₜqₓ = 1 − l_{x+t}/lₓ,   ₜpₓ = l_{x+t}/lₓ.

Contratos (C_f capital de fallecimiento, C_s capital de supervivencia):

  temporal          ₘ|A¹ₓ:ₙ⌉     C_f·v^{m+i} con _{m+i−1|}qₓ (i = 1..n);  0 con ₘqₓ + ₘ₊ₙpₓ
  vida_entera       ₘ|Aₓ         igual con n = w + 1 − x − m;              0 con ₘqₓ (si m > 0)
  capital_diferido  Aₓ:ₙ⌉ (¹ sobre n) = ₙEₓ    C_s·vⁿ con ₙpₓ;  0 con ₙqₓ   (sin diferimiento)
  mixto             ₘ|Aₓ:ₙ⌉      0 con ₘqₓ (si m > 0);  C_f·v^{m+i} con _{m+i−1|}qₓ (i = 1..n);
                                 C_s·v^{m+n} con ₘ₊ₙpₓ.   Prima pura = C_f·ₘ|A¹ₓ:ₙ⌉ + C_s·ₘ₊ₙEₓ

Los valores iguales se agrupan (p. ej. mixto con C_f = C_s y m = 0: C·vⁿ con ₙ₋₁|qₓ + ₙpₓ) y la
distribución se ordena por valor para F, cuantiles, VaR y TVaR.
"""
import math

import descuento
import rentas
import tablas
from distribucion import agregar, momentos, metricas, prima

W = rentas.W
TIPOS = ("temporal", "vida_entera", "capital_diferido", "mixto")
NOMBRES = dict(temporal="Temporal", vida_entera="Vida entera", capital_diferido="Capital diferido", mixto="Mixto")
CON_FALLECIMIENTO = ("temporal", "vida_entera", "mixto")
CON_SUPERVIVENCIA = ("capital_diferido", "mixto")
CON_DIFERIMIENTO = ("temporal", "vida_entera", "mixto")
CON_DURACION = ("temporal", "capital_diferido", "mixto")


def _ent(v):
    return math.isfinite(v) and abs(v - round(v)) < 1e-9


def validar(tipo, x, n, m, I, Cf, Cs, need_year=False, year=None):
    if tipo not in TIPOS:
        return "Tipo de contrato desconocido."
    if not _ent(x) or x < 0 or x > W:
        return "La edad x debe ser un número entero entre 0 y 120."
    if tipo in CON_DURACION and (not _ent(n) or n < 1):
        return "La duración n debe ser un número entero de años mayor o igual que 1."
    if tipo in CON_DIFERIMIENTO and (not _ent(m) or m < 0):
        return "El diferimiento m debe ser un número entero de años mayor o igual que 0."
    if tipo == "vida_entera" and round(x) + round(m) >= W + 1:
        return "Con este diferimiento la cobertura empezaría tras la edad máxima: x + m debe ser menor que w + 1 = 121."
    e = descuento.validar_interes(I)
    if e:
        return e
    if tipo in CON_FALLECIMIENTO and (not math.isfinite(Cf) or Cf <= 0):
        return "El capital de fallecimiento debe ser positivo."
    if tipo in CON_SUPERVIVENCIA and (not math.isfinite(Cs) or Cs <= 0):
        return "El capital de supervivencia debe ser positivo."
    if need_year and (not math.isfinite(year) or abs(year - round(year)) > 1e-9 or year < 1900 or year > 2200):
        return "El año de cálculo debe ser un entero entre 1900 y 2200."
    return None


validar_tabla = rentas.validar_tabla


def distribucion(l, tipo, x, n, m, I, Cf, Cs):
    """Eventos del contrato y distribución agregada de Z (filas ordenadas por valor)."""
    x = int(round(x))
    m = int(round(m)) if tipo in CON_DIFERIMIENTO else 0
    n = (W + 1 - x - m) if tipo == "vida_entera" else int(round(n))
    v = descuento.factor(I)
    L = lambda t: tablas.l_at(l, x + t, "lin")  # noqa: E731  (t entero: lectura exacta de l)
    lx = L(0)

    ev = []

    def add(val, prob, t, cap, psym):
        ev.append(dict(val=val, prob=prob, t=t, cap=cap, psym=psym))

    # valor 0: no se paga nada
    if tipo == "temporal":
        add(0.0, (1 - L(m) / lx if m > 0 else 0.0) + L(m + n) / lx, None, None,
            ([("q", m)] if m > 0 else []) + [("p", m + n)])
    elif tipo == "capital_diferido":
        add(0.0, 1 - L(n) / lx, None, None, [("q", n)])
    elif m > 0:  # vida entera y mixto diferidos
        add(0.0, 1 - L(m) / lx, None, None, [("q", m)])
    # fallecimiento en el año m + i: se paga al final, en t = m + i
    if tipo in CON_FALLECIMIENTO:
        for i in range(1, n + 1):
            add(Cf * v(m + i), (L(m + i - 1) - L(m + i)) / lx, m + i, "f", [("dq", m + i - 1)])
    # supervivencia al final del periodo, t = m + n
    if tipo in CON_SUPERVIVENCIA:
        add(Cs * v(m + n), L(m + n) / lx, m + n, "s", [("p", m + n)])

    rows = agregar(ev)
    comp = dict(fallecimiento=sum(e["val"] * e["prob"] for e in ev if e["cap"] == "f"),
                supervivencia=sum(e["val"] * e["prob"] for e in ev if e["cap"] == "s"))
    return dict(eventos=ev, rows=rows, tipo=tipo, x=x, n=n, m=m, I=I, v=1.0 / (1.0 + I),
                Cf=Cf if tipo in CON_FALLECIMIENTO else 0.0, Cs=Cs if tipo in CON_SUPERVIVENCIA else 0.0,
                componentes=comp, p_pago=sum(e["prob"] for e in ev if e["cap"] is not None),
                prob_total=sum(e["prob"] for e in ev))


def calcular(key, sex, year, tipo, x, n, m, I, Cf, Cs, ordenes=(1, 2), alpha=0.0):
    e = validar_tabla(key, sex, year, x)
    if e:
        raise ValueError(e)
    cohort, l = rentas._lx_vector(key, sex, year, x)
    D = distribucion(l, tipo, x, n, m, I, Cf, Cs)
    D["momentos"] = momentos(D["rows"], ordenes)
    D["metricas"] = metricas(D["rows"])
    D["prima"] = prima(D["metricas"]["media"], alpha)
    D["cohort"] = cohort if tablas.is_per(key) else None
    return D

"""
Rentas actuariales: distribución, momentos de orden s y métricas derivadas.

Notación de la asignatura (apuntes de Seguros de Vida):
  · I = tipo efectivo anual, constante;  v = (1 + I)^(−1);  el plazo 1/m se descuenta con v^(1/m).
  · C = cuantía ANUAL. Si se paga c en cada plazo, C = m · c y cada pago vale C/m.
  · Rentas financieras unitarias (C = 1):
        a^(m)_{t⌉} = Σ_{i=1}^{mt} v^{i/m} / m          (postpagable)
        ä^(m)_{t⌉} = Σ_{i=1}^{mt} v^{(i−1)/m} / m      (prepagable)
        k| a^(m)_{t⌉} = v^k · a^(m)_{t⌉}
  · w = 120 es la edad máxima; la renta vitalicia usa n = w + 1 − x − k.

La variable aleatoria se denota con el propio símbolo de la renta. Con N = m·n plazos:

  Prepagable  k|ä^(m)_{x:n⌉}
      0                         con prob. ₖqₓ                      (solo si k > 0)
      k|ä^(m)_{j/m⌉}, j=1..N    con prob. _{k+(j−1)/m | 1/m} qₓ
      al último valor (j = N) se le suma _{k+n} pₓ  (nula en la vitalicia)

  Postpagable  k|a^(m)_{x:n⌉}
      0                         con prob. _{k+1/m} qₓ
      k|a^(m)_{j/m⌉}, j=1..N−1  con prob. _{k+j/m | 1/m} qₓ
      k|a^(m)_{n⌉}              con prob. _{k+n} pₓ  (temporal; en la vitalicia no existe)

Las probabilidades se leen de lₓ (sin productorios):  _{t|h} qₓ = (l_{x+t} − l_{x+t+h}) / lₓ.
Las edades x + t no enteras (t múltiplo de 1/m) usan l interpolada linealmente (UDD).
"""
import math

import tablas

W = 120  # edad máxima de la asignatura (ω = w + 1 = 121, l_121 = 0)
PCTS = (0.05, 0.25, 0.50, 0.75, 0.95, 0.995)
ALPHA = 0.995  # nivel de Solvencia II


def _is_mult(v, m):
    return abs(v * m - round(v * m)) < 1e-9


def validar(x, n, m, k, I, c, vitalicia, need_year=False, year=None):
    if not math.isfinite(x) or x < 0 or x > W or abs(x - round(x)) > 1e-9:
        return "La edad x debe ser un número entero entre 0 y 120."
    if not (isinstance(m, int) and m >= 1):
        return "El número de pagos al año m debe ser un entero positivo."
    if not math.isfinite(k) or k < 0 or not _is_mult(k, m):
        return f"El diferimiento k debe ser ≥ 0 y múltiplo de 1/{m}."
    if not vitalicia and (not math.isfinite(n) or n <= 0 or not _is_mult(n, m)):
        return f"El horizonte n debe ser > 0 y múltiplo de 1/{m}."
    if vitalicia and round(x) + k >= W + 1:
        return "Con este diferimiento nadie llega a cobrar: x + k debe ser menor que w + 1 = 121."
    if not math.isfinite(I) or I <= -1:
        return "El tipo de interés I debe ser mayor que −100 %."
    if not math.isfinite(c) or c <= 0:
        return "La cuantía de cada plazo debe ser positiva."
    if need_year and (not math.isfinite(year) or abs(year - round(year)) > 1e-9 or year < 1900 or year > 2200):
        return "El año de cálculo debe ser un entero entre 1900 y 2200."
    return None


def _lx_vector(key, sex, year, x):
    cohort = (year - math.floor(x)) if tablas.is_per(key) else 0
    return cohort, tablas.build_lx(tablas.mortality_vector(key, sex, cohort))


def validar_tabla(key, sex, year, x):
    """Error si, con la tabla elegida, nadie llega a la edad x (l_x = 0)."""
    _, l = _lx_vector(key, sex, year, x)
    if tablas.l_at(l, round(x), "lin") <= 0:
        return f"Con esta tabla nadie llega a la edad x = {round(x)} (lₓ = 0): elige una edad menor."
    return None


def frac(p, m):
    """Plazo p/m como en los apuntes: '47', '1/12' o '47+1/12'."""
    q, r = divmod(p, m)
    if r == 0:
        return str(q)
    return f"{r}/{m}" if q == 0 else f"{q}+{r}/{m}"


def distribucion(l, x, n, m, k, I, c, pre, vitalicia):
    """Distribución de la renta. Devuelve un dict con las filas (valor, probabilidad) en euros."""
    x = int(round(x)); K = int(round(k * m))
    if vitalicia:
        N = (W + 1 - x) * m - K           # n = w + 1 − x − k
    else:
        N = int(round(n * m))
    n = N / m
    C = m * c
    v = 1.0 / (1.0 + I)
    vk = v ** (K / m)
    L = lambda p: tablas.l_at(l, x + p / m, "lin")  # noqa: E731  (p en plazos de 1/m desde x)
    lx = L(0)

    # Rentas financieras unitarias acumuladas: A[j] = a^(m)_{j/m⌉}, AA[j] = ä^(m)_{j/m⌉}
    A, AA = [0.0], [0.0]
    for i in range(1, N + 1):
        A.append(A[-1] + v ** (i / m) / m)
        AA.append(AA[-1] + v ** ((i - 1) / m) / m)

    rows = []

    def add(pagos, unit, prob, vsym, psym):
        rows.append(dict(pagos=pagos, unit=unit, val=C * unit, prob=prob, vsym=vsym, psym=psym))

    fin = (L(K + N)) / lx  # _{k+n} p_x  (0 en la vitalicia)
    if pre:
        if K > 0:
            add(0, 0.0, 1 - L(K) / lx, ("0",), ("q", None, frac(K, m)))
        for j in range(1, N + 1):
            p = (L(K + j - 1) - L(K + j)) / lx
            ps = ("q", frac(K + j - 1, m), frac(1, m))
            if j == N and not vitalicia:
                p += fin
                ps = ("q+p", frac(K + j - 1, m), frac(1, m), frac(K + N, m))
            add(j, vk * AA[j], p, ("ä", frac(j, m)), ps)
    else:
        add(0, 0.0, 1 - L(K + 1) / lx, ("0",), ("q", None, frac(K + 1, m)))
        for j in range(1, N):
            p = (L(K + j) - L(K + j + 1)) / lx
            add(j, vk * A[j], p, ("a", frac(j, m)), ("q", frac(K + j, m), frac(1, m)))
        if not vitalicia:
            add(N, vk * A[N], fin, ("a", frac(N, m)), ("p", frac(K + N, m)))

    return dict(rows=rows, C=C, c=c, n=n, N=N, k=K / m, K=K, m=m, x=x, v=v, I=I, pre=pre, vitalicia=vitalicia,
                prob_total=sum(r["prob"] for r in rows), p_completa=fin if not vitalicia else 0.0)


def momentos(rows, ordenes):
    """E[Y^s] = Σ valor^s · prob  para cada orden s pedido (en euros^s)."""
    return {s: sum(r["val"] ** s * r["prob"] for r in rows) for s in ordenes}


def cuantil(rows, a):
    """Q(a) = mín { y : F(y) ≥ a }  (distribución discreta)."""
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
    m1, m2, m3, m4 = (momentos(rows, (1, 2, 3, 4))[s] for s in (1, 2, 3, 4))
    var = max(0.0, m2 - m1 ** 2)
    sd = math.sqrt(var)
    # momentos centrales a partir de los ordinarios
    mu3 = m3 - 3 * m1 * m2 + 2 * m1 ** 3
    mu4 = m4 - 4 * m1 * m3 + 6 * m1 ** 2 * m2 - 3 * m1 ** 4
    return dict(media=m1, var=var, sd=sd, cv=sd / m1 if m1 > 0 else float("nan"),
                asim=mu3 / sd ** 3 if sd > 0 else float("nan"),
                curt=mu4 / sd ** 4 if sd > 0 else float("nan"),
                cuantiles={a: cuantil(rows, a) for a in PCTS},
                var995=cuantil(rows, ALPHA), tvar995=tvar(rows, ALPHA))


def calcular(key, sex, year, x, n, m, k, I, c, pre, vitalicia, ordenes=(1, 2)):
    e = validar_tabla(key, sex, year, x)
    if e:
        raise ValueError(e)
    cohort, l = _lx_vector(key, sex, year, x)
    D = distribucion(l, x, n, m, k, I, c, pre, vitalicia)
    D["momentos"] = momentos(D["rows"], ordenes)
    D["metricas"] = metricas(D["rows"])
    D["cohort"] = cohort if tablas.is_per(key) else None
    return D

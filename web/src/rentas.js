/* Rentas actuariales — espejo de rentas.py de la versión Python.

   Notación: I tipo efectivo anual constante, v = (1+I)^−1, cada plazo 1/m se
   descuenta con v^(1/m); C = cuantía ANUAL (C = m·c si se paga c por plazo); w = 120.
       a^(m)_{t⌉} = Σ_{i=1}^{mt} v^{i/m}/m        ä^(m)_{t⌉} = Σ_{i=1}^{mt} v^{(i−1)/m}/m
       k|a^(m)_{t⌉} = v^k · a^(m)_{t⌉}

   Distribución, con N = m·n plazos (vitalicia: n = w + 1 − x − k):
     Prepagable k|ä:   0 con ₖqₓ (si k>0);  k|ä_{j/m⌉} con _{k+(j−1)/m | 1/m}qₓ, j=1..N;
                       al último se le suma _{k+n}pₓ (nula en la vitalicia).
     Postpagable k|a:  0 con _{k+1/m}qₓ;  k|a_{j/m⌉} con _{k+j/m | 1/m}qₓ, j=1..N−1;
                       k|a_{n⌉} con _{k+n}pₓ (solo temporal).
   Probabilidades leídas de l (sin productorios); edades x + j/m con interpolación lineal (UDD). */
import { isPer, cohortOf, mortalityVector, buildLx, lAt } from "./engine.js";
import { factor, validarInteres } from "./descuento.js";
import { momentos, metricas, prima } from "./distribucion.js";
export { PCTS, ALPHA, momentos, cuantil, tvar, metricas } from "./distribucion.js";

export const W = 120;

const isMult = (v, m) => Math.abs(v * m - Math.round(v * m)) < 1e-9;

export function validar({ x, n, m, k, I, c, vit, needYear, year }) {
  if (!Number.isFinite(x) || x < 0 || x > W || Math.abs(x - Math.round(x)) > 1e-9) return "La edad x debe ser un número entero entre 0 y 120.";
  if (!(Number.isInteger(m) && m >= 1)) return "El número de pagos al año m debe ser un entero positivo.";
  if (!Number.isFinite(k) || k < 0 || !isMult(k, m)) return `El diferimiento k debe ser ≥ 0 y múltiplo de 1/${m}.`;
  if (!vit && (!Number.isFinite(n) || n <= 0 || !isMult(n, m))) return `El horizonte n debe ser > 0 y múltiplo de 1/${m}.`;
  if (vit && Math.round(x) + k >= W + 1) return "Con este diferimiento nadie llega a cobrar: x + k debe ser menor que w + 1 = 121.";
  const eI = validarInteres(I);
  if (eI) return eI;
  if (!Number.isFinite(c) || c <= 0) return "La cuantía de cada plazo debe ser positiva.";
  if (needYear && (!Number.isFinite(year) || Math.abs(year - Math.round(year)) > 1e-9 || year < 1900 || year > 2200))
    return "El año de cálculo debe ser un entero entre 1900 y 2200.";
  return null;
}

export function lxVector(key, sex, year, x) {
  const cohort = isPer(key) ? cohortOf(year, x) : null;
  return { cohort, l: buildLx(mortalityVector(key, sex, cohort ?? 0)) };
}

/* Error si, con la tabla elegida, nadie llega a la edad x (l_x = 0) */
export function validarTabla({ key, sex, year, x }) {
  const { l } = lxVector(key, sex, year, x);
  if (!(lAt(l, Math.round(x), "lin") > 0))
    return `Con esta tabla nadie llega a la edad x = ${Math.round(x)} (lₓ = 0): elige una edad menor.`;
  return null;
}

/* Plazo p/m como en los apuntes: "47", "1/12" o "47+1/12" */
export function frac(p, m) {
  const q = Math.floor(p / m), r = p - q * m;
  return r === 0 ? String(q) : q === 0 ? `${r}/${m}` : `${q}+${r}/${m}`;
}

export function distribucion(l, x, n, m, k, I, c, pre, vit) {
  x = Math.round(x);
  const K = Math.round(k * m);
  const N = vit ? (W + 1 - x) * m - K : Math.round(n * m);
  n = N / m;
  const C = m * c, v = 1 / (1 + I), vt = factor(I), vk = vt(K / m); // capa de descuento
  const L = (p) => lAt(l, x + p / m, "lin"); // p en plazos de 1/m desde x
  const lx = L(0);
  const A = [0], AA = [0]; // a^(m)_{j/m⌉}, ä^(m)_{j/m⌉}
  for (let i = 1; i <= N; i++) { A.push(A[i - 1] + vt(i / m) / m); AA.push(AA[i - 1] + vt((i - 1) / m) / m); }

  const rows = [];
  const add = (pagos, unit, prob, vsym, psym) => rows.push({ pagos, unit, val: C * unit, prob, vsym, psym });
  const fin = L(K + N) / lx; // _{k+n} p_x  (0 en la vitalicia)
  if (pre) {
    if (K > 0) add(0, 0, 1 - L(K) / lx, ["0"], ["q", null, frac(K, m)]);
    for (let j = 1; j <= N; j++) {
      let p = (L(K + j - 1) - L(K + j)) / lx, ps = ["q", frac(K + j - 1, m), frac(1, m)];
      if (j === N && !vit) { p += fin; ps = ["q+p", frac(K + j - 1, m), frac(1, m), frac(K + N, m)]; }
      add(j, vk * AA[j], p, ["ä", frac(j, m)], ps);
    }
  } else {
    add(0, 0, 1 - L(K + 1) / lx, ["0"], ["q", null, frac(K + 1, m)]);
    for (let j = 1; j < N; j++) add(j, vk * A[j], (L(K + j) - L(K + j + 1)) / lx, ["a", frac(j, m)], ["q", frac(K + j, m), frac(1, m)]);
    if (!vit) add(N, vk * A[N], fin, ["a", frac(N, m)], ["p", frac(K + N, m)]);
  }
  return { rows, C, c, n, N, k: K / m, K, m, x, v, I, pre, vit,
    probTotal: rows.reduce((s, r) => s + r.prob, 0), pCompleta: vit ? 0 : fin };
}

export function calcular({ key, sex, year, x, n, m, k, I, c, pre, vit, ordenes = [1, 2], alpha = 0 }) {
  const e = validarTabla({ key, sex, year, x });
  if (e) throw new Error(e);
  const { cohort, l } = lxVector(key, sex, year, x);
  const D = distribucion(l, x, n, m, k, I, c, pre, vit);
  D.momentos = momentos(D.rows, ordenes);
  D.metricas = metricas(D.rows);
  D.prima = prima(D.metricas.media, alpha);
  D.cohort = cohort;
  return D;
}

/* "1, 2, 3" o "1-4" → [1,2,3,4]; null si no es válido (enteros 1..12) */
export function parseOrdenes(t) {
  const out = new Set();
  for (let p of String(t).replace(/;/g, ",").split(",")) {
    p = p.trim();
    if (!p) continue;
    const mm = p.match(/^(\d+)\s*-\s*(\d+)$/);
    if (mm) { let a = +mm[1], b = +mm[2]; if (a > b) [a, b] = [b, a]; for (let s = a; s <= b; s++) out.add(s); }
    else if (/^\d+$/.test(p)) out.add(+p);
    else return null;
  }
  const o = [...out].sort((a, b) => a - b);
  return !o.length || o[0] < 1 || o[o.length - 1] > 12 ? null : o;
}

/* Seguros de vida sobre una cabeza — espejo de seguros.py.

   x, n y m enteros; capital de fallecimiento al FINAL del año de fallecimiento; v(t) = (1+I)^−t;
   w = 120. Probabilidades leídas de l: _{t|}qₓ = (l_{x+t} − l_{x+t+1})/lₓ, ₜqₓ = 1 − l_{x+t}/lₓ, ₜpₓ = l_{x+t}/lₓ.
     temporal          ₘ|A¹ₓ:ₙ⌉   C_f·v^{m+i} con _{m+i−1|}qₓ (i=1..n); 0 con ₘqₓ + ₘ₊ₙpₓ
     vida_entera       ₘ|Aₓ       igual con n = w + 1 − x − m; 0 con ₘqₓ (si m > 0)
     capital_diferido  ₙEₓ        C_s·vⁿ con ₙpₓ; 0 con ₙqₓ (sin diferimiento)
     mixto             ₘ|Aₓ:ₙ⌉    0 con ₘqₓ (si m > 0); C_f·v^{m+i} con _{m+i−1|}qₓ; C_s·v^{m+n} con ₘ₊ₙpₓ
   Valores iguales se agrupan; la distribución se ordena por valor. */
import { isPer, lAt } from "./engine.js";
import { factor, validarInteres } from "./descuento.js";
import { agregar, momentos, metricas, prima } from "./distribucion.js";
import { W, validarTabla as vt, lxVector } from "./rentas.js";

export { W };
export const TIPOS = ["temporal", "vida_entera", "capital_diferido", "mixto"];
export const NOMBRES = { temporal: "Temporal", vida_entera: "Vida entera", capital_diferido: "Capital diferido", mixto: "Mixto" };
export const CON_FALLECIMIENTO = ["temporal", "vida_entera", "mixto"];
export const CON_SUPERVIVENCIA = ["capital_diferido", "mixto"];
export const CON_DIFERIMIENTO = ["temporal", "vida_entera", "mixto"];
export const CON_DURACION = ["temporal", "capital_diferido", "mixto"];

const ent = (v) => Number.isFinite(v) && Math.abs(v - Math.round(v)) < 1e-9;

export function validar({ tipo, x, n, m, I, Cf, Cs, needYear, year }) {
  if (!TIPOS.includes(tipo)) return "Tipo de contrato desconocido.";
  if (!ent(x) || x < 0 || x > W) return "La edad x debe ser un número entero entre 0 y 120.";
  if (CON_DURACION.includes(tipo) && (!ent(n) || n < 1)) return "La duración n debe ser un número entero de años mayor o igual que 1.";
  if (CON_DIFERIMIENTO.includes(tipo) && (!ent(m) || m < 0)) return "El diferimiento m debe ser un número entero de años mayor o igual que 0.";
  if (tipo === "vida_entera" && Math.round(x) + Math.round(m) >= W + 1)
    return "Con este diferimiento la cobertura empezaría tras la edad máxima: x + m debe ser menor que w + 1 = 121.";
  const eI = validarInteres(I);
  if (eI) return eI;
  if (CON_FALLECIMIENTO.includes(tipo) && (!Number.isFinite(Cf) || Cf <= 0)) return "El capital de fallecimiento debe ser positivo.";
  if (CON_SUPERVIVENCIA.includes(tipo) && (!Number.isFinite(Cs) || Cs <= 0)) return "El capital de supervivencia debe ser positivo.";
  if (needYear && (!Number.isFinite(year) || Math.abs(year - Math.round(year)) > 1e-9 || year < 1900 || year > 2200))
    return "El año de cálculo debe ser un entero entre 1900 y 2200.";
  return null;
}

export const validarTabla = vt;

export function distribucion(l, tipo, x, n, m, I, Cf, Cs) {
  x = Math.round(x);
  m = CON_DIFERIMIENTO.includes(tipo) ? Math.round(m) : 0;
  n = tipo === "vida_entera" ? W + 1 - x - m : Math.round(n);
  const v = factor(I), L = (t) => lAt(l, x + t, "lin"), lx = L(0);
  const ev = [];
  const add = (val, prob, t, cap, psym) => ev.push({ val, prob, t, cap, psym });
  if (tipo === "temporal") add(0, (m > 0 ? 1 - L(m) / lx : 0) + L(m + n) / lx, null, null, [...(m > 0 ? [["q", m]] : []), ["p", m + n]]);
  else if (tipo === "capital_diferido") add(0, 1 - L(n) / lx, null, null, [["q", n]]);
  else if (m > 0) add(0, 1 - L(m) / lx, null, null, [["q", m]]);
  if (CON_FALLECIMIENTO.includes(tipo))
    for (let i = 1; i <= n; i++) add(Cf * v(m + i), (L(m + i - 1) - L(m + i)) / lx, m + i, "f", [["dq", m + i - 1]]);
  if (CON_SUPERVIVENCIA.includes(tipo)) add(Cs * v(m + n), L(m + n) / lx, m + n, "s", [["p", m + n]]);

  const rows = agregar(ev);
  const sum = (f) => ev.reduce((s, e) => s + f(e), 0);
  return { eventos: ev, rows, tipo, x, n, m, I, v: 1 / (1 + I),
    Cf: CON_FALLECIMIENTO.includes(tipo) ? Cf : 0, Cs: CON_SUPERVIVENCIA.includes(tipo) ? Cs : 0,
    componentes: { fallecimiento: sum((e) => (e.cap === "f" ? e.val * e.prob : 0)), supervivencia: sum((e) => (e.cap === "s" ? e.val * e.prob : 0)) },
    pPago: sum((e) => (e.cap !== null ? e.prob : 0)), probTotal: sum((e) => e.prob) };
}

export function calcular({ key, sex, year, tipo, x, n, m, I, Cf, Cs, ordenes = [1, 2], alpha = 0 }) {
  const e = validarTabla({ key, sex, year, x });
  if (e) throw new Error(e);
  const { cohort, l } = lxVector(key, sex, year, x);
  const D = distribucion(l, tipo, x, n, m, I, Cf, Cs);
  D.momentos = momentos(D.rows, ordenes);
  D.metricas = metricas(D.rows);
  D.prima = prima(D.metricas.media, alpha);
  D.cohort = isPer(key) ? cohort : null;
  return D;
}

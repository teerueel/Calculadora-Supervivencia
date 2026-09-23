/* Motor de cálculo — espejo de tablas.py y modelos.py de la versión Python.
   Todo parte de l: tablas → l_x construida con las q publicadas; modelos continuos →
   l_x = 100 000 · S(x) con S = e^{−H}; Heligman–Pollard → l_x desde sus q_x.        */
import { TABLES, PRESETS } from "./data.js";

export const OMEGA = 121;
export const RADIX = 100000;
export const isPer = (k) => TABLES[k].kind === "per";

/* ============================ Tablas ============================ */
export function mortalityVector(key, sex, cohort) {
  const t = TABLES[key];
  const q = [];
  for (let y = 0; y <= 120; y++) {
    let v;
    if (t.kind === "per") {
      const { qb, lam } = t.data[sex];
      v = (qb[y] / 1000) * Math.exp(-lam[y] * (cohort + y - t.base));
    } else v = t.data[sex][y] / 1000;
    q.push(Math.min(1, Math.max(0, v)));
  }
  q[120] = 1;
  return q;
}

export function buildLx(q) {
  const l = [RADIX];
  for (let y = 0; y <= 120; y++) l.push(l[y] * (1 - q[y]));
  return l;
}

/* l en edad real con la interpolación elegida: "lin" (UDD) o "exp" (fuerza constante) */
export function lAt(l, a, metodo) {
  if (!(a >= 0) || a >= OMEGA) return 0;
  const y = Math.floor(a + 1e-12), s = a - y;
  if (s < 1e-12) return l[y];
  const ly = l[y], ly1 = l[y + 1];
  if (metodo === "lin") return ly - s * (ly - ly1);
  if (ly <= 0) return 0;
  return ly * Math.pow(ly1 / ly, s);
}

export function muAt(q, a, metodo) {
  if (!(a >= 0) || a >= OMEGA - 1) return null;
  const y = Math.floor(a + 1e-12), s = a - y, qy = q[y];
  if (metodo === "lin") return s * qy < 1 ? qy / (1 - s * qy) : null;
  return qy < 1 ? -Math.log(1 - qy) : null;
}

function segIntegral(ly, ly1, s0, metodo) {
  if (metodo === "lin") return ly * (1 - s0) - ((ly - ly1) * (1 - s0 * s0)) / 2;
  if (ly <= 0) return 0;
  const p = ly1 / ly;
  if (p <= 0) return 0;
  if (Math.abs(p - 1) < 1e-15) return ly * (1 - s0);
  return (ly * (p - Math.pow(p, s0))) / Math.log(p);
}

export function eCompleteL(l, x, metodo) {
  const lx = lAt(l, x, metodo);
  if (!(lx > 0)) return 0;
  const y = Math.floor(x + 1e-12);
  let tot = segIntegral(l[y], l[y + 1], x - y, metodo);
  for (let k = y + 1; k < OMEGA; k++) tot += segIntegral(l[k], l[k + 1], 0, metodo);
  return tot / lx;
}

export const cohortOf = (year, x) => year - Math.floor(x);

export function tableModel(key, sex, year, x, metodo) {
  const cohort = isPer(key) ? cohortOf(year, x) : null;
  const q = mortalityVector(key, sex, cohort ?? 0);
  const l = buildLx(q);
  return {
    kind: "table", q, l, cohort, metodo,
    L: (a) => lAt(l, a, metodo),
    mu: (a) => muAt(q, a, metodo),
    ecx: (xx) => eCompleteL(l, xx, metodo),
  };
}

/* ============================ Modelos paramétricos ============================ */
function erfc(x) {
  const z = Math.abs(x), t = 1 / (1 + 0.5 * z);
  const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 +
    t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
  return x >= 0 ? r : 2 - r;
}
const Phi = (z) => 0.5 * erfc(-z / Math.SQRT2);

const P = (k, sym, min, max, scale, desc) => ({ k, sym, min, max, scale, desc });

export const MODELS = {
  exponencial: { name: "Exponencial", family: "Clásicos", kind: "cont", formula: "μₓ = λ",
    params: [P("lam", "λ", 1e-4, 0.5, "log", "fuerza de mortalidad constante")],
    mu: (x, p) => p.lam, H: (x, p) => p.lam * x },
  demoivre: { name: "De Moivre", family: "Clásicos", kind: "cont", formula: "μₓ = 1 / (ω − x)",
    params: [P("w", "ω", 50, 160, "lin", "edad límite")],
    mu: (x, p) => (x < p.w ? 1 / (p.w - x) : Infinity), H: (x, p) => (x < p.w ? -Math.log(1 - x / p.w) : Infinity) },
  gompertz: { name: "Gompertz", family: "Clásicos", kind: "cont", formula: "μₓ = B · cˣ",
    params: [P("B", "B", 1e-7, 1e-3, "log", "nivel de la mortalidad"), P("c", "c", 1.01, 1.2, "lin", "ritmo de envejecimiento")],
    mu: (x, p) => p.B * Math.pow(p.c, x), H: (x, p) => (p.B / Math.log(p.c)) * (Math.pow(p.c, x) - 1) },
  makeham: { name: "Makeham", family: "Clásicos", kind: "cont", formula: "μₓ = A + B · cˣ",
    params: [P("A", "A", 0, 5e-3, "lin", "mortalidad independiente de la edad"), P("B", "B", 1e-7, 1e-3, "log", "nivel de la senescencia"),
      P("c", "c", 1.01, 1.2, "lin", "ritmo de envejecimiento")],
    mu: (x, p) => p.A + p.B * Math.pow(p.c, x), H: (x, p) => p.A * x + (p.B / Math.log(p.c)) * (Math.pow(p.c, x) - 1) },
  weibull: { name: "Weibull", family: "Clásicos", kind: "cont", formula: "μₓ = (β/θ) · (x/θ)^(β−1)",
    params: [P("be", "β", 0.3, 15, "lin", "forma"), P("th", "θ", 20, 120, "lin", "escala (edad característica)")],
    mu: (x, p) => (x > 0 || p.be >= 1 ? (p.be / p.th) * Math.pow(x / p.th, p.be - 1) : Infinity), H: (x, p) => Math.pow(x / p.th, p.be) },
  perks: { name: "Perks", family: "Logísticos", kind: "cont", formula: "μₓ = (A + B · cˣ) / (1 + D · cˣ)",
    params: [P("A", "A", 0, 5e-3, "lin", "mortalidad independiente de la edad"), P("B", "B", 1e-7, 1e-3, "log", "nivel de la senescencia"),
      P("c", "c", 1.01, 1.2, "lin", "ritmo de envejecimiento"), P("D", "D", 1e-7, 1e-3, "log", "freno logístico")],
    mu: (x, p) => { const r = Math.pow(p.c, x); return (p.A + p.B * r) / (1 + p.D * r); },
    H: (x, p) => p.A * x + ((p.B - p.A * p.D) / (p.D * Math.log(p.c))) * (Math.log1p(p.D * Math.pow(p.c, x)) - Math.log1p(p.D)) },
  kannisto: { name: "Kannisto", family: "Logísticos", kind: "cont", formula: "μₓ = a·eᵇˣ / (1 + a·eᵇˣ)",
    params: [P("a", "a", 1e-9, 1e-2, "log", "nivel"), P("b", "b", 0.03, 0.2, "lin", "ritmo de crecimiento")],
    mu: (x, p) => { const r = p.a * Math.exp(p.b * x); return r / (1 + r); },
    H: (x, p) => (Math.log1p(p.a * Math.exp(p.b * x)) - Math.log1p(p.a)) / p.b },
  thiele: { name: "Thiele", family: "Curva completa", kind: "cont", formula: "μₓ = a₁e^(−b₁x) + a₂e^(−½b₂(x−c)²) + a₃e^(b₃x)",
    params: [P("a1", "a₁", 1e-4, 0.2, "log", "nivel infantil"), P("b1", "b₁", 0.05, 5, "lin", "descenso infantil"),
      P("a2", "a₂", 1e-6, 1e-2, "log", "intensidad de la joroba"), P("b2", "b₂", 1e-4, 0.2, "log", "concentración de la joroba"),
      P("c", "c", 10, 40, "lin", "edad de la joroba"), P("a3", "a₃", 1e-7, 1e-3, "log", "nivel de la senescencia"),
      P("b3", "b₃", 0.05, 0.2, "lin", "ritmo de envejecimiento")],
    mu: (x, p) => p.a1 * Math.exp(-p.b1 * x) + p.a2 * Math.exp(-0.5 * p.b2 * (x - p.c) ** 2) + p.a3 * Math.exp(p.b3 * x),
    H: (x, p) => (p.a1 / p.b1) * (1 - Math.exp(-p.b1 * x))
      + p.a2 * Math.sqrt((2 * Math.PI) / p.b2) * (Phi(Math.sqrt(p.b2) * (x - p.c)) - Phi(-Math.sqrt(p.b2) * p.c))
      + (p.a3 / p.b3) * (Math.exp(p.b3 * x) - 1) },
  siler: { name: "Siler", family: "Curva completa", kind: "cont", formula: "μₓ = a₁e^(−b₁x) + a₂ + a₃e^(b₃x)",
    params: [P("a1", "a₁", 1e-4, 0.2, "log", "nivel infantil"), P("b1", "b₁", 0.05, 5, "lin", "descenso infantil"),
      P("a2", "a₂", 0, 5e-3, "lin", "mortalidad de fondo"), P("a3", "a₃", 1e-7, 1e-3, "log", "nivel de la senescencia"),
      P("b3", "b₃", 0.05, 0.2, "lin", "ritmo de envejecimiento")],
    mu: (x, p) => p.a1 * Math.exp(-p.b1 * x) + p.a2 + p.a3 * Math.exp(p.b3 * x),
    H: (x, p) => (p.a1 / p.b1) * (1 - Math.exp(-p.b1 * x)) + p.a2 * x + (p.a3 / p.b3) * (Math.exp(p.b3 * x) - 1) },
  heligman_pollard: { name: "Heligman–Pollard", family: "Curva completa", kind: "disc", formula: "qₓ/pₓ = A^((x+B)^C) + D·e^(−E(ln x − ln F)²) + G·Hˣ",
    params: [P("A", "A", 1e-5, 0.05, "log", "nivel de la mortalidad infantil"), P("B", "B", 1e-5, 0.5, "log", "desplazamiento de edad"),
      P("C", "C", 0.01, 0.5, "lin", "velocidad del descenso infantil"), P("D", "D", 1e-6, 1e-2, "log", "intensidad de la joroba"),
      P("E", "E", 0.5, 40, "lin", "dispersión de la joroba (inversa)"), P("F", "F", 10, 40, "lin", "edad de la joroba"),
      P("G", "G", 1e-7, 1e-3, "log", "nivel de la senescencia"), P("H", "H", 1.01, 1.2, "lin", "ritmo de envejecimiento")] },
};
export const MODEL_KEYS = Object.keys(MODELS);
export const MODEL_FAMILIES = ["Clásicos", "Logísticos", "Curva completa"];

export function hpQ(x, p) {
  let r = Math.pow(p.A, Math.pow(x + p.B, p.C)) + p.G * Math.pow(p.H, x);
  if (x > 0) r += p.D * Math.exp(-p.E * (Math.log(x) - Math.log(p.F)) ** 2);
  return r / (1 + r);
}

export const defaultParams = (key, sex) => ({ ...PRESETS[key][sex] });
export const allDefaults = () => Object.fromEntries(MODEL_KEYS.map((k) => [k, { H: defaultParams(k, "H"), M: defaultParams(k, "M") }]));

export function paramModel(key, p, metodo) {
  const m = MODELS[key];
  if (m.kind === "disc") {
    const q = [];
    for (let y = 0; y <= 120; y++) q.push(Math.min(1, Math.max(0, hpQ(y, p))));
    q[120] = 1;
    const l = buildLx(q);
    return { kind: "disc", q, l, metodo, L: (a) => lAt(l, a, metodo), mu: (a) => muAt(q, a, metodo), ecx: (x) => eCompleteL(l, x, metodo) };
  }
  const S = (a) => { const h = m.H(a, p); return Number.isFinite(h) ? Math.exp(-h) : 0; };
  const mu = (a) => { const v = m.mu(a, p); return Number.isFinite(v) ? v : null; };
  const ecx = (x) => {
    if (key === "exponencial") return 1 / p.lam;
    if (key === "demoivre") return Math.max(0, (p.w - x) / 2);
    const sx = S(x);
    if (!(sx > 0)) return 0;
    const h = 0.05; let tot = 0, t = 0, f0 = 1;
    while (t < 500) {
      const f1 = S(x + t + h) / sx, f2 = S(x + t + 2 * h) / sx;
      tot += (h / 3) * (f0 + 4 * f1 + f2); t += 2 * h; f0 = f2;
      if (f2 < 1e-12) break;
    }
    return tot;
  };
  return { kind: "cont", L: (a) => RADIX * S(a), mu, ecx };
}

/* ============================ Resultados comunes ============================ */
export function results(M, x, n, m) {
  const lx = M.L(x), lxn = M.L(x + n), lxm = M.L(x + m), lxmn = M.L(x + m + n);
  const npx = lx > 0 ? lxn / lx : NaN;
  const r = { lx, lxn, lxm, lxmn, npx, nqx: 1 - npx, mnqx: (lxm - lxmn) / lx, mqx: 1 - lxm / lx, mnpx: lxmn / lx, ecx: M.ecx(x) };
  if (M.kind !== "cont") { let e = 0; for (let k = 1; x + k < OMEGA; k++) e += M.L(x + k) / lx; r.ex = e; }
  return r;
}

export function curveData(M, x, step = 0.25) {
  const lx = M.L(x), out = [];
  for (let t = 0; x + t <= OMEGA + 1e-9; t = Math.round((t + step) * 1e9) / 1e9) {
    const p = lx > 0 ? M.L(x + t) / lx : NaN;
    out.push({ t, S: p, F: 1 - p, mu: M.mu(x + t) });
  }
  return out;
}

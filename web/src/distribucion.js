/* Variable aleatoria discreta del valor actual (rentas y seguros) y su prima — espejo de
   distribucion.py. Filas con val y prob; los cuantiles exigen filas ORDENADAS por valor.
     E[Z^s] = Σ z^s·prob;  Q(a) = mín{z : F(z) ≥ a};  TVaR_a = (1/(1−a)) ∫_a^1 Q(u) du;
     prima recargada (1 + α)·E[Z], con α ≥ 0 libre. */
export const PCTS = [0.05, 0.25, 0.5, 0.75, 0.95, 0.995];
export const ALPHA = 0.995; // Solvencia II

/* Ordena por valor y junta los valores iguales (|Δ| ≤ 1e-12·máx(1,|z|)) */
export function agregar(eventos) {
  const out = [];
  for (const e of [...eventos].sort((a, b) => a.val - b.val)) {
    const u = out[out.length - 1];
    if (u && Math.abs(e.val - u.val) <= 1e-12 * Math.max(1, Math.abs(e.val))) { u.prob += e.prob; u.eventos.push(e); }
    else out.push({ val: e.val, prob: e.prob, eventos: [e] });
  }
  return out;
}

/* E[Z^s] = Σ valor^s · prob (en euros^s) */
export function momentos(rows, ordenes) {
  const o = {};
  for (const s of ordenes) o[s] = rows.reduce((t, r) => t + Math.pow(r.val, s) * r.prob, 0);
  return o;
}

/* Q(a) = mín { z : F(z) ≥ a } */
export function cuantil(rows, a) {
  let F = 0;
  for (const r of rows) { F += r.prob; if (F >= a - 1e-12) return r.val; }
  return rows[rows.length - 1].val;
}

/* TVaR_a = (1/(1−a)) ∫_a^1 Q(u) du  (válida también con átomos) */
export function tvar(rows, a) {
  let F0 = 0, t = 0;
  for (const r of rows) { const F1 = F0 + r.prob; t += r.val * Math.max(0, F1 - Math.max(F0, a)); F0 = F1; }
  return t / (1 - a);
}

/* Momentos centrales directos μ_k = Σ (z − E[Z])^k·prob (estables); σ ≤ 1e-12·máx(1,|E[Z]|) se toma 0 */
export function metricas(rows) {
  const m1 = momentos(rows, [1])[1];
  const mu = (k) => rows.reduce((t, r) => t + Math.pow(r.val - m1, k) * r.prob, 0);
  const mu3 = mu(3), mu4 = mu(4);
  let vr = Math.max(0, mu(2)), sd = Math.sqrt(vr);
  if (sd <= 1e-12 * Math.max(1, Math.abs(m1))) vr = sd = 0;
  const cuantiles = Object.fromEntries(PCTS.map((a) => [a, cuantil(rows, a)]));
  return { media: m1, var: vr, sd, cv: m1 > 0 ? sd / m1 : NaN, asim: sd > 0 ? mu3 / sd ** 3 : NaN, curt: sd > 0 ? mu4 / sd ** 4 : NaN,
    cuantiles, var995: cuantil(rows, ALPHA), tvar995: tvar(rows, ALPHA) };
}

export function validarRecargo(alpha) {
  if (!Number.isFinite(alpha) || alpha < 0) return "El recargo de seguridad α debe ser un porcentaje mayor o igual que 0.";
  return null;
}

/* Prima pura, importe del recargo α·E[Z] y prima recargada (1 + α)·E[Z] */
export function prima(pura, alpha) {
  return { alpha, pura, recargo: alpha * pura, recargada: (1 + alpha) * pura };
}

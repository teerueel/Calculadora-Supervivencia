/* Rentas actuariales (motor web): distribución, prima pura y métricas. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mortalityVector, buildLx, lAt, isPer } from "../../web/src/engine.js";
import { calcular, validar, validarTabla, W, PCTS } from "../../web/src/rentas.js";

const COMBOS = [["pasem_gen_2", "M"], ["per_ind_2", "H"], ["per_col_1", "M"], ["pasem_dec_1", "H"]];

function* casos([key, sex]) {
  for (const x of [0, 40, 65, 100, 108, 119, 120]) for (const m of [1, 4, 12]) for (const k of [0, 2.5, 10])
    for (const n of [1, 25.5]) for (const I of [0, 0.0195, 0.05]) for (const pre of [true, false]) for (const vit of [true, false]) {
      if (vit && n !== 1) continue;
      if (validar({ x, n, m, k, I, c: 1, vit }) || validarTabla({ key, sex, year: 2026, x })) continue;
      yield { key, sex, year: 2026, x, n, m, k, I, c: 1, pre, vit };
    }
}

/* Prima pura directa: Σ v^{k+j/m} · _{k+j/m} p_x / m  (j = 0..N−1 prepagable, 1..N postpagable), por C = m·c */
function valorActuarial({ key, sex, year, x, n, m, k, I, c, pre, vit }) {
  const l = buildLx(mortalityVector(key, sex, isPer(key) ? year - x : 0));
  const N = vit ? (W + 1 - x) * m - Math.round(k * m) : Math.round(n * m), v = 1 / (1 + I), lx = lAt(l, x, "lin");
  let tot = 0;
  for (let j = pre ? 0 : 1; j <= (pre ? N - 1 : N); j++) tot += Math.pow(v, k + j / m) * lAt(l, x + k + j / m, "lin") / lx;
  return m * c * tot / m;
}

for (const combo of COMBOS) {
  test(`${combo.join(" ")}: Σ prob = 1, valores crecientes y media = prima pura`, () => {
    let nCasos = 0;
    for (const P of casos(combo)) {
      nCasos++;
      const D = calcular({ ...P, ordenes: [1, 2, 3, 4] });
      const probs = D.rows.map((r) => r.prob), vals = D.rows.map((r) => r.val);
      assert.ok(probs.every((p) => p >= -1e-12));
      assert.ok(Math.abs(probs.reduce((a, b) => a + b, 0) - 1) < 1e-12);
      assert.ok(vals.every((v, i) => i === 0 || v >= vals[i - 1] - 1e-12));
      const va = valorActuarial(P), M = D.metricas;
      assert.ok(Math.abs(M.media - va) <= 1e-12 * Math.max(1, va), `${JSON.stringify(P)}: ${M.media} vs ${va}`);
      // métricas
      assert.ok(M.var >= 0 && Math.abs(M.var - (D.momentos[2] - D.momentos[1] ** 2)) <= 1e-9 * Math.max(1, D.momentos[2]));
      const cs = PCTS.map((a) => M.cuantiles[a]);
      assert.ok(cs.every((v, i) => i === 0 || v >= cs[i - 1]));
      assert.ok(M.tvar995 >= M.var995 - 1e-9);
    }
    assert.ok(nCasos > 50);
  });
}

test("l_x = 0 es un error, no un resultado", () => {
  assert.equal(validarTabla({ key: "pasem_gen_2", sex: "M", year: 2026, x: 110 }), null);
  assert.match(validarTabla({ key: "pasem_gen_2", sex: "M", year: 2026, x: 111 }), /lₓ = 0/);
  assert.throws(() => calcular({ key: "pasem_gen_2", sex: "M", year: 2026, x: 111, n: 1, m: 1, k: 0, I: 0.02, c: 1, pre: true, vit: false }));
});

test("validación de parámetros", () => {
  const base = { x: 30, n: 10, m: 4, k: 0, I: 0.02, c: 1, vit: false };
  assert.equal(validar(base), null);
  assert.match(validar({ ...base, x: 30.5 }), /edad x/);
  assert.match(validar({ ...base, m: 0 }), /pagos al año/);
  assert.match(validar({ ...base, k: 0.3 }), /diferimiento k/);
  assert.match(validar({ ...base, n: 10.1 }), /horizonte n/);
  assert.match(validar({ ...base, I: -1 }), /tipo de interés/);
  assert.match(validar({ ...base, c: 0 }), /cuantía/);
  assert.match(validar({ ...base, needYear: true, year: 1800 }), /año/);
});

/* Seguros de vida (motor web): distribución de Z, prima por conmutación, relación con rentas. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mortalityVector, buildLx, isPer } from "../../web/src/engine.js";
import * as S from "../../web/src/seguros.js";
import * as R from "../../web/src/rentas.js";
import { validarRecargo } from "../../web/src/distribucion.js";

const COMBOS = [["pasem_gen_2", "M"], ["per_ind_2", "H"], ["per_col_1", "M"], ["pasem_dec_1", "H"]];

function* casos([key, sex]) {
  for (const tipo of S.TIPOS) for (const x of [0, 40, 65, 100, 108, 119]) for (const n of [1, 10, 35]) for (const m of [0, 3, 20])
    for (const I of [0, 0.0195, 0.05]) for (const [Cf, Cs] of [[1, 1], [1000, 2500]]) {
      if ((tipo === "vida_entera" && n !== 1) || (tipo === "capital_diferido" && m !== 0) || (tipo !== "mixto" && Cf !== 1)) continue;
      if (S.validar({ tipo, x, n, m, I, Cf, Cs }) || S.validarTabla({ key, sex, year: 2026, x })) continue;
      yield { key, sex, year: 2026, tipo, x, n, m, I, Cf, Cs };
    }
}

/* Funciones de conmutación: D_y = v^y l_y, M_y = Σ_{z≥y} v^{z+1} d_z */
function conmutacion({ key, sex, year, tipo, x, n, m, I, Cf, Cs }) {
  const l = buildLx(mortalityVector(key, sex, isPer(key) ? year - x : 0)), v = 1 / (1 + I);
  const ly = (y) => (y >= 0 && y < l.length ? l[y] : 0), D = (y) => v ** y * ly(y);
  const M = (y) => { let s = 0; for (let z = y; z < l.length; z++) s += v ** (z + 1) * (ly(z) - ly(z + 1)); return s; };
  if (tipo === "temporal") return Cf * (M(x + m) - M(x + m + n)) / D(x);
  if (tipo === "vida_entera") return Cf * M(x + m) / D(x);
  if (tipo === "capital_diferido") return Cs * D(x + n) / D(x);
  return Cf * (M(x + m) - M(x + m + n)) / D(x) + Cs * D(x + m + n) / D(x);
}

for (const combo of COMBOS) {
  test(`${combo.join(" ")}: Σ prob = 1, valores crecientes y media = conmutación`, () => {
    let nCasos = 0;
    for (const P of casos(combo)) {
      nCasos++;
      const D = S.calcular({ ...P, ordenes: [1, 2], alpha: 0.1 });
      const probs = D.rows.map((r) => r.prob), vals = D.rows.map((r) => r.val);
      assert.ok(probs.every((p) => p >= -1e-12));
      assert.ok(Math.abs(probs.reduce((a, b) => a + b, 0) - 1) < 1e-12);
      assert.ok(vals.every((v, i) => i === 0 || v > vals[i - 1]));
      const va = conmutacion(P), M = D.metricas;
      assert.ok(Math.abs(M.media - va) <= 1e-12 * Math.max(1, va), `${JSON.stringify(P)}: ${M.media} vs ${va}`);
      assert.ok(Math.abs(D.componentes.fallecimiento + D.componentes.supervivencia - M.media) <= 1e-12 * Math.max(1, M.media));
      assert.ok(Math.abs(D.prima.recargada - 1.1 * M.media) <= 1e-12 * Math.max(1, M.media));
      assert.ok(M.tvar995 >= M.var995 - 1e-9);
    }
    assert.ok(nCasos > 50);
  });

  test(`${combo.join(" ")}: Aₓ = 1 − d·äₓ y Aₓ:ₙ⌉ = 1 − d·äₓ:ₙ⌉`, () => {
    const [key, sex] = combo;
    for (const x of [0, 30, 65, 100]) for (const I of [0, 0.0195, 0.05]) {
      if (S.validarTabla({ key, sex, year: 2026, x })) continue;
      const d = 1 - 1 / (1 + I), base = { key, sex, year: 2026, x, I };
      const A = S.calcular({ ...base, tipo: "vida_entera", n: 0, m: 0, Cf: 1, Cs: 0 }).metricas.media;
      const a = R.calcular({ ...base, n: 1, m: 1, k: 0, c: 1, pre: true, vit: true }).metricas.media;
      assert.ok(Math.abs(A - (1 - d * a)) < 1e-12);
      for (const n of [1, 10, 35]) {
        const Am = S.calcular({ ...base, tipo: "mixto", n, m: 0, Cf: 1, Cs: 1 }).metricas.media;
        const an = R.calcular({ ...base, n, m: 1, k: 0, c: 1, pre: true, vit: false }).metricas.media;
        assert.ok(Math.abs(Am - (1 - d * an)) < 1e-12);
      }
    }
  });
}

test("validación de parámetros y recargo", () => {
  const base = { tipo: "temporal", x: 30, n: 10, m: 0, I: 0.02, Cf: 1, Cs: 1 };
  assert.equal(S.validar(base), null);
  assert.match(S.validar({ ...base, x: 30.5 }), /edad x/);
  assert.match(S.validar({ ...base, n: 0 }), /duración n/);
  assert.match(S.validar({ ...base, m: 1.5 }), /diferimiento m/);
  assert.match(S.validar({ ...base, tipo: "vida_entera", x: 100, m: 21 }), /edad máxima/);
  assert.match(S.validar({ ...base, I: -1 }), /tipo de interés/);
  assert.match(S.validar({ ...base, Cf: 0 }), /fallecimiento/);
  assert.match(S.validar({ ...base, tipo: "mixto", Cs: 0 }), /supervivencia/);
  assert.equal(S.validar({ ...base, tipo: "capital_diferido", m: 7.5, Cf: 0 }), null);
  assert.match(validarRecargo(-0.01), /recargo/);
  assert.equal(validarRecargo(0), null);
  assert.throws(() => S.calcular({ key: "pasem_gen_2", sex: "M", year: 2026, ...base, x: 111 }));
});

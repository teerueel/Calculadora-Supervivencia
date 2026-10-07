/* Modelos paramétricos (motor web): S(x), μ = H', identidad de control y e̊_x. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { MODELS, MODEL_KEYS, paramModel, results, defaultParams, RADIX } from "../../web/src/engine.js";

const SEXOS = ["M", "H"], TOL = 1e-12;
const CONTINUOS = MODEL_KEYS.filter((k) => MODELS[k].kind === "cont");

test("hay diez modelos con presets por sexo", () => {
  assert.equal(MODEL_KEYS.length, 10);
  for (const k of MODEL_KEYS) for (const s of SEXOS)
    assert.deepEqual(Object.keys(defaultParams(k, s)).sort(), MODELS[k].params.map((p) => p.k).sort());
});

for (const key of MODEL_KEYS) for (const sex of SEXOS) {
  test(`${key} ${sex}: S(0) = 1, S no creciente e identidad de control`, () => {
    for (const met of ["lin", "exp"]) {
      const M = paramModel(key, defaultParams(key, sex), met);
      assert.ok(Math.abs(M.L(0) / RADIX - 1) < TOL);
      let prev = Infinity;
      for (let a = 0; a <= 121; a += 0.25) { const v = M.L(a); assert.ok(v <= prev + 1e-9); prev = v; }
      for (const x of [0, 0.5, 30, 65, 85.75, 100]) for (const n of [0, 1, 2.5, 10]) for (const m of [0, 1, 5.25]) {
        const r = results(M, x, n, m);
        if (!(r.lx > 0)) continue;
        assert.ok(Math.abs(r.mqx + r.mnqx + r.mnpx - 1) < TOL && Math.abs(r.npx + r.nqx - 1) < TOL);
      }
    }
  });
}

for (const key of CONTINUOS) for (const sex of SEXOS) {
  test(`${key} ${sex}: μ(x) = H'(x)`, () => {
    const p = defaultParams(key, sex), h = 1e-5;
    for (let a = 0.5; a <= 110; a += a < 1 ? 0.5 : 1) {
      if (key === "demoivre" && a + h >= p.w) break;
      const num = (MODELS[key].H(a + h, p) - MODELS[key].H(a - h, p)) / (2 * h), mu = MODELS[key].mu(a, p);
      assert.ok(Math.abs(mu - num) <= 1e-6 * Math.max(1, mu), `${a}: ${mu} vs ${num}`);
    }
  });

  test(`${key} ${sex}: e̊_x frente a integración numérica`, () => {
    const M = paramModel(key, defaultParams(key, sex), "lin");
    for (const x of [0, 40, 65.5, 90]) {
      const sx = M.L(x);
      if (!(sx > 0)) continue;
      let tot = 0, t = 0;
      const h = 0.01;
      for (;;) {
        let s = 0;
        for (let i = 0; i <= 1000; i++) s += (i === 0 || i === 1000 ? 1 : i % 2 ? 4 : 2) * M.L(x + t + i * h);
        tot += (h / 3) * s / sx; t += 10;
        if (M.L(x + t) / sx < 1e-13 || t > 20000) break;
      }
      assert.ok(Math.abs(M.ecx(x) - tot) < 1e-6 * Math.max(1, tot), `${x}: ${M.ecx(x)} vs ${tot}`);
    }
  });
}

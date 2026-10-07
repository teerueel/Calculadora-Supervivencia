/* Tablas de mortalidad (motor web): l_x, identidad de control y esperanzas de vida. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { TABLES } from "../../web/src/data.js";
import { tableModel, results, mortalityVector, buildLx, lAt, muAt, isPer, RADIX } from "../../web/src/engine.js";

const TABLAS = Object.keys(TABLES), SEXOS = ["M", "H"], METODOS = ["lin", "exp"];
const EDADES = [0, 0.5, 17, 30, 47.3, 65, 85.75, 100, 110.5, 119, 120];
const PLAZOS = [0, 1, 2.5, 10, 30], DIFS = [0, 1, 5.25, 20];
const años = (k) => (isPer(k) ? [1960, 2026, 2100] : [2026]);
const TOL = 1e-12;

test("el catálogo tiene las 9 tablas", () => assert.equal(TABLAS.length, 9));

for (const key of TABLAS) for (const sex of SEXOS) {
  test(`${key} ${sex}: vector q y l_x`, () => {
    for (const año of años(key)) for (const x of [0, 40, 65, 90]) {
      const q = mortalityVector(key, sex, año - x), l = buildLx(q);
      assert.equal(q.length, 121); assert.equal(l.length, 122);
      assert.ok(q.every((v) => v >= 0 && v <= 1));
      assert.equal(q[120], 1); assert.equal(l[0], RADIX); assert.equal(l[121], 0);
      for (let y = 0; y <= 120; y++) {
        assert.ok(l[y + 1] <= l[y]);
        assert.ok(Math.abs(l[y + 1] - l[y] * (1 - q[y])) <= 1e-9);
      }
    }
  });

  for (const met of METODOS) {
    test(`${key} ${sex} ${met}: _m q_x + _{m|n} q_x + _{m+n} p_x = 1`, () => {
      const fallos = [];
      for (const año of años(key)) for (const x of EDADES) {
        const M = tableModel(key, sex, año, x, met);
        for (const n of PLAZOS) for (const m of DIFS) {
          const r = results(M, x, n, m);
          if (!(r.lx > 0)) continue;
          const s = r.mqx + r.mnqx + r.mnpx;
          if (Math.abs(s - 1) > TOL || Math.abs(r.npx + r.nqx - 1) > TOL) fallos.push([año, x, n, m, s]);
        }
      }
      assert.deepEqual(fallos, []);
    });

    test(`${key} ${sex} ${met}: l interpolada y μ = −d ln l / da`, () => {
      const q = mortalityVector(key, sex, 2026), l = buildLx(q), h = 1e-6;
      for (let y = 0; y < 119; y++) {
        assert.equal(lAt(l, y, met), l[y]);
        if (q[y] >= 1) continue;
        for (const s of [0.2, 0.5, 0.8]) {
          const esperado = met === "lin" ? 1 - s * q[y] : Math.pow(1 - q[y], s);
          if (l[y] > 0) assert.ok(Math.abs(lAt(l, y + s, met) / l[y] - esperado) < 1e-12);
          const num = -(Math.log(lAt(l, y + s + h, met)) - Math.log(lAt(l, y + s - h, met))) / (2 * h);
          const mu = muAt(q, y + s, met);
          assert.ok(Math.abs(mu - num) <= 1e-5 * Math.max(1, mu), `${y + s}: ${mu} vs ${num}`);
        }
      }
    });
  }

  test(`${key} ${sex}: con UDD y x entera, e̊_x = e_x + ½`, () => {
    for (const año of años(key)) for (let x = 0; x <= 120; x += 5) {
      const r = results(tableModel(key, sex, año, x, "lin"), x, 1, 0);
      if (r.lx > 0) assert.ok(Math.abs(r.ecx - (r.ex + 0.5)) < 1e-9, `${año} ${x}`);
      else assert.ok(Number.isNaN(r.npx) && Number.isNaN(r.ex), "l_x = 0 no da resultado");
    }
  });
}

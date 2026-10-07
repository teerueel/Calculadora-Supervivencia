/* Volcado del motor web para la prueba de paridad con Python (tests/python/test_paridad.py).
   Lee por la entrada estándar un JSON con listas de casos y escribe los resultados en JSON.
   NaN e ±Infinity se escriben como null. */
import { TABLES, PRESETS } from "../../web/src/data.js";
import { tableModel, paramModel, results, mortalityVector, buildLx, defaultParams, MODEL_KEYS } from "../../web/src/engine.js";
import { calcular, validar, validarTabla, frac } from "../../web/src/rentas.js";

const CAMPOS = ["lx", "lxn", "lxm", "lxmn", "npx", "nqx", "mnqx", "mqx", "mnpx", "ecx", "ex"];
const pick = (r) => Object.fromEntries(CAMPOS.filter((k) => k in r).map((k) => [k, r[k]]));

let txt = "";
process.stdin.setEncoding("utf8");
for await (const chunk of process.stdin) txt += chunk;
const E = JSON.parse(txt);
const out = {};

if (E.datos) out.datos = Object.fromEntries(Object.entries(TABLES).map(([k, t]) => [k, t.data]));
if (E.presets) out.presets = Object.fromEntries(MODEL_KEYS.map((k) => [k, PRESETS[k]]));

out.vectores = (E.vectores || []).map(([key, sex, cohort]) => {
  const q = mortalityVector(key, sex, cohort);
  return { q, l: buildLx(q) };
});

out.tablas = (E.tablas || []).map(([key, sex, year, met, x, n, m]) =>
  pick(results(tableModel(key, sex, year, x, met), x, n, m)));

out.modelos = (E.modelos || []).map(([key, sex, met, x, n, m]) => {
  const M = paramModel(key, defaultParams(key, sex), met);
  return { ...pick(results(M, x, n, m)), mu: M.mu(x) };
});

out.rentas = (E.rentas || []).map(([key, sex, year, x, n, m, k, I, c, pre, vit]) => {
  const D = calcular({ key, sex, year, x, n, m, k, I, c, pre, vit, ordenes: [1, 2, 3, 4] });
  return { rows: D.rows.map((r) => [r.pagos, r.val, r.prob]), momentos: D.momentos, metricas: D.metricas,
    N: D.N, n: D.n, k: D.k, cohort: D.cohort };
});

out.validar = (E.validar || []).map(([x, n, m, k, I, c, vit, needYear, year]) =>
  validar({ x, n, m, k, I, c, vit, needYear, year }));
out.validarTabla = (E.validarTabla || []).map(([key, sex, year, x]) => validarTabla({ key, sex, year, x }));
out.frac = (E.frac || []).map(([p, m]) => frac(p, m));

process.stdout.write(JSON.stringify(out, (k, v) => (typeof v === "number" && !Number.isFinite(v) ? null : v)));

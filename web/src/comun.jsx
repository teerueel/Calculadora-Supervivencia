/* Piezas comunes de las pestañas de rentas y seguros: formato, gráficas de la distribución del
   valor actual, tablas de momentos y métricas, prima (pura, recargo, recargada), interés técnico. */
import React from "react";
import { PCTS } from "./distribucion.js";
import { TIPO_TECNICO } from "./descuento.js";

/* ============================ Formato ============================ */
const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
export const sup = (e) => String(e).split("").map((c) => SUP[c]).join("");
export const parseNum = (s) => { const t = String(s).trim().replace(/\s/g, "").replace(",", "."); return /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(t) ? Number(t) : NaN; };
export const fmtA = (v) => v.toLocaleString("es-ES", { maximumFractionDigits: 4, useGrouping: false });
/* importes; notación científica a partir de 10⁹ (momentos de orden alto) */
export const fmtEur = (v, d = 2) => {
  if (!Number.isFinite(v)) return "—";
  if (Math.abs(v) < 1e9) return v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: "always" });
  const e = Math.floor(Math.log10(Math.abs(v)));
  return (v / 10 ** e).toLocaleString("es-ES", { minimumFractionDigits: 6, maximumFractionDigits: 6 }) + "·10" + sup(e);
};
export const fmtN = (v, d = 6) => (Number.isFinite(v) ? v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d }) : "—");
export const fmtPct = (a) => (a * 100).toLocaleString("es-ES", { maximumFractionDigits: 4 });

export { parseOrdenes } from "./rentas.js";
export const ERR_ORDENES = "Los órdenes s deben ser enteros entre 1 y 12, separados por comas o como rango (1-4).";

/* ============================ Gráficas (SVG) ============================ */
function niceTicks(lo, hi, k = 5) {
  const sp = hi - lo || 1, st0 = sp / k, mg = 10 ** Math.floor(Math.log10(st0));
  const st = [1, 2, 2.5, 5, 10].map((f) => f * mg).find((s) => s >= st0);
  const o = [];
  for (let v = Math.ceil(lo / st) * st; v <= hi + 1e-9; v += st) o.push(v);
  return o;
}

/* rows ordenadas por valor creciente, con val y prob */
export function DistChart({ title, rows, M, kind, logp }) {
  const W_ = 560, H = 290, pl = 70, pr = 34, pt = 12, pb = 48, iw = W_ - pl - pr, ih = H - pt - pb;
  const pos = rows.filter((r) => r.prob > 0);
  const xmax = Math.max(...rows.map((r) => r.val)) * 1.02 || 1, X = (v) => pl + (v / xmax) * iw;
  const tx = { fontSize: 15, fill: "var(--muted)", fontFamily: "'Public Sans',system-ui,sans-serif" };
  let Y, yt, yl, body;
  if (kind === "pmf") {
    const pmin = Math.min(...pos.map((r) => r.prob)), pmax = Math.max(...pos.map((r) => r.prob));
    if (logp) {
      const lo = Math.min(Math.floor(Math.log10(pmin)), -1), hi = 0, stp = Math.max(1, Math.ceil((hi - lo) / 6));
      Y = (p) => pt + ih * (1 - (Math.log10(p) - lo) / (hi - lo));
      yt = []; for (let e = hi; e >= lo; e -= stp) yt.push(10 ** e);
      yl = (p) => "10" + sup(Math.round(Math.log10(p)));
    } else {
      Y = (p) => pt + ih * (1 - p / (pmax * 1.08));
      yt = niceTicks(0, pmax * 1.08); yl = (p) => p.toLocaleString("es-ES", { maximumSignificantDigits: 3 });
    }
    body = (<g>
      {pos.map((r, i) => <line key={i} x1={X(r.val)} x2={X(r.val)} y1={pt + ih} y2={Y(r.prob)} style={{ stroke: "var(--mu)", strokeWidth: 1.2 }} />)}
      {pos.map((r, i) => <circle key={"c" + i} cx={X(r.val)} cy={Y(r.prob)} r={2.4} style={{ fill: "var(--mu)" }} />)}
    </g>);
  } else {
    Y = (p) => pt + ih * (1 - p / 1.03); yt = [0, 0.2, 0.4, 0.6, 0.8, 1]; yl = (p) => p.toLocaleString("es-ES");
    let F = 0, d = `M${X(rows[0].val)},${Y(0)}`;
    rows.forEach((r) => { d += ` L${X(r.val)},${Y(F)}`; F += r.prob; d += ` L${X(r.val)},${Y(F)}`; });
    d += ` L${X(xmax)},${Y(F)}`;
    body = <path d={d} style={{ fill: "none", stroke: "var(--surv)", strokeWidth: 1.8 }} />;
  }
  const grid = { stroke: "var(--rule)", strokeDasharray: "2 3" };
  return (
    <figure className="chart">
      <figcaption>{title}</figcaption>
      <svg viewBox={`0 0 ${W_} ${H}`} width="100%" role="img" aria-label={title}>
        {yt.map((v, i) => (<g key={"y" + i}><line x1={pl} x2={W_ - pr} y1={Y(v)} y2={Y(v)} style={grid} /><text x={pl - 7} y={Y(v) + 5} textAnchor="end" style={tx}>{yl(v)}</text></g>))}
        {niceTicks(0, xmax).map((v, i) => (<g key={"x" + i}><line x1={X(v)} x2={X(v)} y1={pt} y2={pt + ih} style={grid} />
          <text x={X(v)} y={pt + ih + 20} textAnchor="middle" style={tx}>{v.toLocaleString("es-ES", { useGrouping: "always" })}</text></g>))}
        <text x={pl + iw / 2} y={H - 4} textAnchor="middle" style={tx}>valor actual (€)</text>
        {body}
        <line x1={X(M.media)} x2={X(M.media)} y1={pt} y2={pt + ih} style={{ stroke: "var(--ink)", strokeDasharray: "5 4", strokeWidth: 1.1 }} />
        <line x1={X(M.var995)} x2={X(M.var995)} y1={pt} y2={pt + ih} style={{ stroke: "var(--death)", strokeDasharray: "1.5 3", strokeWidth: 1.6 }} />
        <rect x={pl} y={pt} width={iw} height={ih} style={{ fill: "none", stroke: "var(--rule)" }} />
      </svg>
    </figure>
  );
}

export function DistCharts({ rows, M, logp, setLogp, SegCtl, Z }) {
  return (<>
    <div className="fc-row" style={{ justifyContent: "flex-end", marginBottom: 8 }}>
      <span style={{ fontFamily: "'Public Sans',sans-serif", fontSize: 13, color: "var(--muted)" }}>Escala de la probabilidad:{" "}</span>
      <SegCtl small label="Escala" value={logp} onChange={setLogp} options={[["log", "Log"], ["lin", "Lineal"]]} />
    </div>
    <div className="charts">
      <DistChart title={`Función de masa P(${Z} = ${Z.toLowerCase()})`} rows={rows} M={M} kind="pmf" logp={logp === "log"} />
      <DistChart title={`Función de distribución F(${Z.toLowerCase()})`} rows={rows} M={M} kind="cdf" />
    </div>
    <p className="caption">Línea discontinua: media (prima pura única). Línea punteada roja: VaR al 99,5 %.</p>
  </>);
}

/* ============================ Tablas de resultados ============================ */
export function PrimaCard({ P, Z }) {
  const filas = [
    ["Prima pura única", `E[${Z}]`, P.pura],
    ["Recargo de seguridad", `α · E[${Z}], con α = ${fmtPct(P.alpha)} %`, P.recargo],
    ["Prima recargada", `(1 + α) · E[${Z}]`, P.recargada],
  ];
  return (
    <section className="card">
      <h3>Prima única</h3>
      <div className="tablewrap flat"><table className="ltab rtab">
        <thead><tr><th className="l">Concepto</th><th className="l">Definición</th><th>Importe (€)</th></tr></thead>
        <tbody>{filas.map(([a, b, v], i) => (
          <tr key={a} style={i === 2 ? { fontWeight: 600 } : undefined}><td className="l">{a}</td><td className="l rdef">{b}</td><td>{fmtEur(v)}</td></tr>
        ))}</tbody>
      </table></div>
      <p className="pnote">El recargo α lo fija el usuario; la calculadora no impone ningún principio de cálculo de primas.</p>
    </section>
  );
}

export function MomentosCard({ momentos, Sym }) {
  return (
    <section className="card">
      <h3>Momentos de orden s</h3>
      <div className="tablewrap flat"><table className="ltab rtab">
        <thead><tr><th className="l">s</th><th className="l">Momento</th><th>Valor (€<sup>s</sup>)</th></tr></thead>
        <tbody>{Object.entries(momentos).map(([s, v]) => (
          <tr key={s}><td className="l">{s}</td><td className="l">E[ (<Sym />)<sup>{s}</sup> ]</td><td>{fmtEur(v)}</td></tr>
        ))}</tbody>
      </table></div>
    </section>
  );
}

export function MetricasCard({ M, Z }) {
  const met = [
    ["Media", `E[${Z}] = prima pura única`, fmtEur(M.media) + " €"],
    ["Varianza", `E[(${Z} − E[${Z}])²]`, fmtEur(M.var) + " €²"],
    ["Desviación típica", `σ = √Var(${Z})`, fmtEur(M.sd) + " €"],
    ["Coeficiente de variación", `σ / E[${Z}]`, fmtN(M.cv)],
    ["Asimetría", `E[(${Z} − E[${Z}])³] / σ³`, fmtN(M.asim)],
    ["Curtosis", `E[(${Z} − E[${Z}])⁴] / σ⁴`, Number.isFinite(M.curt) ? `${fmtN(M.curt)} (exceso ${fmtN(M.curt - 3)})` : "—"],
    ["VaR 99,5 %", `Q(0,995) = mín{ ${Z.toLowerCase()} : F(${Z.toLowerCase()}) ≥ 0,995 }`, fmtEur(M.var995) + " €"],
    ["TVaR 99,5 %", "(1/0,005) ∫ Q(u) du entre 0,995 y 1", fmtEur(M.tvar995) + " €"],
  ];
  return (
    <section className="card">
      <h3>Métricas derivadas</h3>
      <div className="tablewrap flat"><table className="ltab rtab">
        <thead><tr><th className="l">Métrica</th><th className="l">Definición</th><th>Valor</th></tr></thead>
        <tbody>{met.map(([a, b, v]) => <tr key={a}><td className="l">{a}</td><td className="l rdef">{b}</td><td>{v}</td></tr>)}</tbody>
      </table></div>
      <div className="tablewrap flat" style={{ marginTop: 10 }}><table className="ltab rtab">
        <thead><tr>{PCTS.map((a) => <th key={a}>Q({(a * 100).toLocaleString("es-ES")}{" "}%)</th>)}</tr></thead>
        <tbody><tr>{PCTS.map((a) => <td key={a}>{fmtEur(M.cuantiles[a])}</td>)}</tr></tbody>
      </table></div>
      {!(M.sd > 0) && <p className="pnote">Distribución degenerada (un único valor): sin asimetría ni curtosis.</p>}
    </section>
  );
}

/* ============================ Interés técnico y recargo ============================ */
export const TT_TXT = fmtPct(TIPO_TECNICO.I);

export function InteresRecargo({ id, iS, setI, aS, setA, Field }) {
  const esTT = Math.abs(parseNum(iS) / 100 - TIPO_TECNICO.I) < 1e-12;
  return (
    <div className="block">
      <h2 className="ptitle">Interés y recargo</h2>
      <div className="grid2">
        <Field id={`${id}-i`} label="Interés técnico I (%)" value={iS} onChange={setI} />
        <Field id={`${id}-a`} label="Recargo α (%)" value={aS} onChange={setA} />
      </div>
      <p className="pnote">
        {esTT ? "Por defecto, " : <><button type="button" className="ghost small" onClick={() => setI(TT_TXT)}>Volver a {TT_TXT} %</button>{" "}</>}
        {TT_TXT} %: tipo máximo de la DGSFP para la provisión de seguros de vida en {TIPO_TECNICO.año} ({TIPO_TECNICO.ref}). Editable.
      </p>
      <p className="pnote">Descuento v = (1 + I)<sup>−1</sup>. Prima recargada = (1 + α) · prima pura.</p>
    </div>
  );
}

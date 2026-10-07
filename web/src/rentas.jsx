/* Pestaña «Rentas actuariales». Los controles comunes (SegCtl, Field, TableSelect, TableTags, Sym)
   se reciben de App.jsx por props para no duplicarlos. */
import React, { useMemo, useState } from "react";
import { TABLES } from "./data.js";
import { isPer, cohortOf } from "./engine.js";
import { W, PCTS, validar, calcular, parseOrdenes, frac } from "./rentas.js";

/* ============================ Formato ============================ */
const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const sup = (e) => String(e).split("").map((c) => SUP[c]).join("");
const parseNum = (s) => { const t = String(s).trim().replace(/\s/g, "").replace(",", "."); return /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(t) ? Number(t) : NaN; };
const fmtA = (v) => v.toLocaleString("es-ES", { maximumFractionDigits: 4, useGrouping: false });
/* importes; notación científica a partir de 10⁹ (momentos de orden alto) */
const fmtEur = (v, d = 2) => {
  if (!Number.isFinite(v)) return "—";
  if (Math.abs(v) < 1e9) return v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d, useGrouping: "always" });
  const e = Math.floor(Math.log10(Math.abs(v)));
  return (v / 10 ** e).toLocaleString("es-ES", { minimumFractionDigits: 6, maximumFractionDigits: 6 }) + "·10" + sup(e);
};
const fmtN = (v, d = 6) => (Number.isFinite(v) ? v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d }) : "—");

/* ============================ Notación ============================ */
/* k|ä^(m)_{sub ang⌉}: superíndice (m) y subíndice apilados; ángulo actuarial con borde superior y derecho */
function RSym({ k, base, m, sub, ang }) {
  return (
    <span className="sym rsym-a">
      {k && k !== "0" && <sub className="pre">{k}|</sub>}
      <span className="base">{base}</span>
      <span className="rs-ss">
        <span className="rs-sup">{m !== 1 ? `(${m})` : "\u00A0"}</span>
        <span className="rs-sub">{sub}{ang != null && <span className="ang">{ang}</span>}</span>
      </span>
    </span>
  );
}
const Renta = ({ pre, m, k, n, vit, x }) => <RSym k={k} base={pre ? "ä" : "a"} m={m} sub={vit ? x : x + ":"} ang={vit ? null : n} />;

function Prob({ ps, x, Sym }) {
  if (ps[0] === "q") return ps[1] == null ? <Sym pre={ps[2]} base="q" post={x} /> : <Sym pre={`${ps[1]}|${ps[2]}`} base="q" post={x} />;
  if (ps[0] === "p") return <Sym pre={ps[1]} base="p" post={x} />;
  return <><Sym pre={`${ps[1]}|${ps[2]}`} base="q" post={x} /> + <Sym pre={ps[3]} base="p" post={x} /></>;
}

/* ============================ Gráficas (SVG) ============================ */
function niceTicks(lo, hi, k = 5) {
  const sp = hi - lo || 1, st0 = sp / k, mg = 10 ** Math.floor(Math.log10(st0));
  const st = [1, 2, 2.5, 5, 10].map((f) => f * mg).find((s) => s >= st0);
  const o = [];
  for (let v = Math.ceil(lo / st) * st; v <= hi + 1e-9; v += st) o.push(v);
  return o;
}

function DistChart({ title, rows, M, kind, logp }) {
  const W_ = 560, H = 290, pl = 70, pr = 34, pt = 12, pb = 48, iw = W_ - pl - pr, ih = H - pt - pb;
  const pos = rows.filter((r) => r.prob > 0);
  const xmax = Math.max(...rows.map((r) => r.val)) * 1.02 || 1, X = (v) => pl + (v / xmax) * iw;
  const tx = { fontSize: 15, fill: "var(--muted)", fontFamily: "'Public Sans',system-ui,sans-serif" };
  let Y, yt, yl, body;
  if (kind === "pmf") {
    const pmin = Math.min(...pos.map((r) => r.prob)), pmax = Math.max(...pos.map((r) => r.prob));
    if (logp) {
      const lo = Math.floor(Math.log10(pmin)), hi = 0, stp = Math.max(1, Math.ceil((hi - lo) / 6));
      Y = (p) => pt + ih * (1 - (Math.log10(p) - lo) / (hi - lo));
      yt = []; for (let e = hi; e >= lo; e -= stp) yt.push(10 ** e);
      yl = (p) => "10" + sup(Math.round(Math.log10(p)));
    } else {
      Y = (p) => pt + ih * (1 - p / (pmax * 1.08));
      yt = niceTicks(0, pmax * 1.08); yl = (p) => p.toLocaleString("es-ES", { maximumSignificantDigits: 3 });
    }
    body = (<g>
      {pos.map((r, i) => <line key={i} x1={X(r.val)} x2={X(r.val)} y1={pt + ih} y2={Y(r.prob)} style={{ stroke: "var(--mu)", strokeWidth: 1.2 }} />)}
      {pos.map((r, i) => <circle key={"c" + i} cx={X(r.val)} cy={Y(r.prob)} r={2} style={{ fill: "var(--mu)" }} />)}
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

/* ============================ Pestaña ============================ */
const M_OPTS = [["1", "1 · anual"], ["2", "2 · semestral"], ["3", "3 · cuatrimestral"], ["4", "4 · trimestral"], ["6", "6 · bimestral"], ["12", "12 · mensual"]];

export default function Rentas({ ui }) {
  const { Sym, SegCtl, Field, TableSelect, TableTags } = ui;
  const [key, setKey] = useState("per_ind_2");
  const [sex, setSex] = useState("H");
  const [yearS, setYear] = useState("2026");
  const [xS, setX] = useState("65");
  const [dur, setDur] = useState("tmp");
  const [nS, setN] = useState("20");
  const [kS, setK] = useState("0");
  const [mS, setM] = useState("12");
  const [tipo, setTipo] = useState("pre");
  const [cS, setC] = useState("1000");
  const [iS, setI] = useState("3");
  const [oS, setO] = useState("1, 2, 3");
  const [showD, setShowD] = useState(false);
  const [logp, setLogp] = useState("log");

  const per = isPer(key), vit = dur === "vit", pre = tipo === "pre", m = +mS;
  const x = parseNum(xS), n = parseNum(nS), k = parseNum(kS), year = parseNum(yearS), c = parseNum(cS), I = parseNum(iS) / 100;
  const ordenes = parseOrdenes(oS);
  let err = validar({ x, n, m, k, I, c, vit, needYear: per, year });
  if (!err && !ordenes) err = "Los órdenes s deben ser enteros entre 1 y 12, separados por comas o como rango (1-4).";

  const D = useMemo(() => (err ? null : calcular({ key, sex, year: per ? Math.round(year) : 2019, x, n, m, k, I, c, pre, vit, ordenes })),
    [err, key, sex, per, year, x, n, m, k, I, c, pre, vit, oS]); // eslint-disable-line react-hooks/exhaustive-deps

  const M = D && D.metricas;
  const xs = D ? fmtA(D.x) : "x", ks = D ? fmtA(D.k) : "", ns = D ? fmtA(D.n) : "n";
  const S = () => <Renta pre={pre} m={m} k={ks} n={ns} vit={vit} x={xs} />;

  const panel = (
    <aside className="panel" aria-label="Parámetros">
      <div className="block">
        <h2 className="ptitle">Tabla</h2>
        <div className="field"><label htmlFor="r-tabla">Tabla de mortalidad</label><TableSelect id="r-tabla" value={key} onChange={setKey} /></div>
        <TableTags k={key} />
      </div>
      <div className="block">
        <h2 className="ptitle">Asegurado</h2>
        <div className="field"><span className="flabel">Sexo</span><SegCtl label="Sexo" value={sex} onChange={setSex} options={[["H", "Hombre"], ["M", "Mujer"]]} /></div>
        <div className="grid2">
          <Field id="r-x" label="Edad x" value={xS} onChange={setX} />
          {per && <Field id="r-y" label="Año de cálculo" value={yearS} onChange={setYear} />}
        </div>
        <p className="pnote">{per && Number.isFinite(x) && Number.isFinite(year) ? `Generación ${cohortOf(year, x)}.` : "Tabla estática: no depende del año (base 2019)."}</p>
      </div>
      <div className="block">
        <h2 className="ptitle">Renta</h2>
        <div className="field"><SegCtl label="Duración" value={dur} onChange={setDur} options={[["tmp", "Temporal"], ["vit", "Vitalicia"]]} /></div>
        <div className="grid2">
          {!vit && <Field id="r-n" label="Horizonte n" value={nS} onChange={setN} />}
          <Field id="r-k" label="Diferimiento k" value={kS} onChange={setK} />
        </div>
        <div className="field">
          <label htmlFor="r-m">Pagos al año m</label>
          <select id="r-m" value={mS} onChange={(e) => setM(e.target.value)}>{M_OPTS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>
        </div>
        <div className="field"><SegCtl label="Tipo de pago" value={tipo} onChange={setTipo} options={[["pre", "Prepagable"], ["post", "Postpagable"]]} /></div>
        <p className="pnote">{vit ? `Vitalicia: n = w + 1 − x − k${D ? ` = ${ns} años` : ""}.` : `n y k admiten múltiplos de 1/${m}.`}</p>
      </div>
      <div className="block">
        <h2 className="ptitle">Cuantía e interés</h2>
        <div className="grid2">
          <Field id="r-c" label="Cuantía por plazo (€)" value={cS} onChange={setC} />
          <Field id="r-i" label="Interés I (%)" value={iS} onChange={setI} />
        </div>
        <p className="pnote">
          {Number.isFinite(c) && <>Cuantía anual C = m · c = {fmtEur(m * c)} €. </>}
          Descuento v = (1 + I)<sup>−1</sup>{m > 1 && <>; cada plazo se descuenta con v<sup>1/{m}</sup></>}.
        </p>
      </div>
      <div className="block">
        <h2 className="ptitle">Momentos</h2>
        <Field id="r-o" label="Órdenes s" value={oS} onChange={setO} />
        <p className="pnote">Lista o rango de enteros entre 1 y 12, p. ej. «1, 2, 3» o «1-4».</p>
        <p className="pnote">Las edades x + j/m no enteras usan interpolación lineal de l (UDD).</p>
      </div>
    </aside>
  );

  if (err) return <div className="layout">{panel}<main className="main"><div className="error" role="alert">{err}</div></main></div>;

  let acc = 0;
  const F = D.rows.map((r) => (acc += r.prob));
  const met = [
    ["Media", "E[Y] = prima pura única", fmtEur(M.media) + " €"],
    ["Varianza", "E[Y²] − E[Y]²", fmtEur(M.var) + " €²"],
    ["Desviación típica", "σ = √Var(Y)", fmtEur(M.sd) + " €"],
    ["Coeficiente de variación", "σ / E[Y]", fmtN(M.cv)],
    ["Asimetría", "E[(Y − E[Y])³] / σ³", fmtN(M.asim)],
    ["Curtosis", "E[(Y − E[Y])⁴] / σ⁴", `${fmtN(M.curt)} (exceso ${fmtN(M.curt - 3)})`],
    ["VaR 99,5 %", "Q(0,995) = mín{ y : F(y) ≥ 0,995 }", fmtEur(M.var995) + " €"],
    ["TVaR 99,5 %", "(1/0,005) ∫ Q(u) du entre 0,995 y 1", fmtEur(M.tvar995) + " €"],
  ];
  const kRow = frac(D.K, m);

  return (
    <div className="layout">
      {panel}
      <main className="main">
        <p className="context">
          {sex === "H" ? "Hombre" : "Mujer"} de {xs} años, {TABLES[key].label}.{" "}
          {per ? `Generación ${D.cohort}, año de cálculo ${Math.round(year)}. ` : "Tabla estática, año base 2019. "}
          Hasta {D.N} pagos {pre ? "prepagables" : "postpagables"} de {fmtEur(c)} € {D.k > 0 ? `tras ${ks} años de diferimiento.` : "sin diferimiento."}
        </p>

        <section className="card results">
          <div className="rrow rhead" style={{ "--accent": "var(--ink)" }}>
            <div className="rsym rsym-big"><span className="rs-c">{fmtEur(D.C)} · </span><S /></div>
            <div className="rtext"><p className="rdesc">Prima pura única: E[ C · <S /> ]</p></div>
            <div className="rval">
              <span className="rnum">{fmtEur(M.media)} €</span>
              <span className="rpct">Prob. de cobrar la renta completa: {vit ? "0 (vitalicia)" : fmtN(D.pCompleta)}</span>
            </div>
          </div>
        </section>

        <section className="card">
          <h3>Momentos de orden s</h3>
          <div className="tablewrap flat"><table className="ltab rtab">
            <thead><tr><th className="l">s</th><th className="l">Momento</th><th>Valor (€<sup>s</sup>)</th></tr></thead>
            <tbody>{Object.entries(D.momentos).map(([s, v]) => (
              <tr key={s}><td className="l">{s}</td><td className="l">E[ (C · <S />)<sup>{s}</sup> ]</td><td>{fmtEur(v)}</td></tr>
            ))}</tbody>
          </table></div>
        </section>

        <section className="card">
          <h3>Métricas derivadas</h3>
          <div className="tablewrap flat"><table className="ltab rtab">
            <thead><tr><th className="l">Métrica</th><th className="l">Definición</th><th>Valor</th></tr></thead>
            <tbody>{met.map(([a, b, v]) => <tr key={a}><td className="l">{a}</td><td className="l rdef">{b}</td><td>{v}</td></tr>)}</tbody>
          </table></div>
          <div className="tablewrap flat" style={{ marginTop: 10 }}><table className="ltab rtab">
            <thead><tr>{PCTS.map((a) => <th key={a}>Q({(a * 100).toLocaleString("es-ES")}{"\u00A0"}%)</th>)}</tr></thead>
            <tbody><tr>{PCTS.map((a) => <td key={a}>{fmtEur(M.cuantiles[a])}</td>)}</tr></tbody>
          </table></div>
        </section>

        <div className="fc-row" style={{ justifyContent: "flex-end", marginBottom: 8 }}>
          <span style={{ fontFamily: "'Public Sans',sans-serif", fontSize: 13, color: "var(--muted)" }}>Escala de la probabilidad:{"\u00A0"}</span>
          <SegCtl small label="Escala" value={logp} onChange={setLogp} options={[["log", "Log"], ["lin", "Lineal"]]} />
        </div>
        <div className="charts">
          <DistChart title="Función de masa P(Y = y)" rows={D.rows} M={M} kind="pmf" logp={logp === "log"} />
          <DistChart title="Función de distribución F(y)" rows={D.rows} M={M} kind="cdf" />
        </div>
        <p className="caption">Línea discontinua: media (prima pura única). Línea punteada roja: VaR al 99,5 %.</p>

        <section className="card">
          <button type="button" className="ghost" aria-expanded={showD} onClick={() => setShowD((s) => !s)}>
            {showD ? "Ocultar" : "Mostrar"} la distribución ({D.rows.length} valores)
          </button>
          {showD && (
            <div className="tablewrap"><table className="ltab rtab">
              <thead><tr>{["Pagos", "Valor", "Probabilidad", "Valor (€)", "Prob.", "F(y)"].map((t, i) => <th key={t} className={i === 1 || i === 2 ? "l" : ""}>{t}</th>)}</tr></thead>
              <tbody>{D.rows.map((r, i) => (
                <tr key={i}>
                  <td>{r.pagos}</td>
                  <td className="l rcell">{r.vsym[0] === "0" ? "0" : <RSym k={kRow} base={r.vsym[0]} m={m} sub="" ang={r.vsym[1]} />}</td>
                  <td className="l rcell"><Prob ps={r.psym} x={xs} Sym={Sym} /></td>
                  <td>{fmtEur(r.val)}</td><td>{fmtN(r.prob, 8)}</td><td>{fmtN(F[i], 8)}</td>
                </tr>
              ))}</tbody>
            </table></div>
          )}
        </section>
      </main>
    </div>
  );
}


/* Pestaña «Rentas actuariales». Los controles comunes (SegCtl, Field, TableSelect, TableTags, Sym)
   se reciben de App.jsx por props para no duplicarlos; las piezas comunes con seguros, de comun.jsx. */
import React, { useMemo, useState } from "react";
import { TABLES } from "./data.js";
import { isPer, cohortOf } from "./engine.js";
import { validar, validarTabla, calcular, frac } from "./rentas.js";
import { validarRecargo } from "./distribucion.js";
import { parseNum, parseOrdenes, ERR_ORDENES, fmtA, fmtEur, fmtN, DistCharts, PrimaCard, MomentosCard, MetricasCard, InteresRecargo, TT_TXT } from "./comun.jsx";

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
  const [iS, setI] = useState(TT_TXT);
  const [aS, setA] = useState("0");
  const [oS, setO] = useState("1, 2, 3");
  const [showD, setShowD] = useState(false);
  const [logp, setLogp] = useState("log");

  const per = isPer(key), vit = dur === "vit", pre = tipo === "pre", m = +mS;
  const x = parseNum(xS), n = parseNum(nS), k = parseNum(kS), year = parseNum(yearS), c = parseNum(cS), I = parseNum(iS) / 100, alpha = parseNum(aS) / 100;
  const ordenes = parseOrdenes(oS);
  let err = validar({ x, n, m, k, I, c, vit, needYear: per, year });
  if (!err) err = validarTabla({ key, sex, year: per ? Math.round(year) : 2019, x });
  if (!err) err = validarRecargo(alpha);
  if (!err && !ordenes) err = ERR_ORDENES;

  const D = useMemo(() => (err ? null : calcular({ key, sex, year: per ? Math.round(year) : 2019, x, n, m, k, I, c, pre, vit, ordenes, alpha })),
    [err, key, sex, per, year, x, n, m, k, I, c, pre, vit, oS, alpha]); // eslint-disable-line react-hooks/exhaustive-deps

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
        <h2 className="ptitle">Cuantía</h2>
        <Field id="r-c" label="Cuantía por plazo c (€)" value={cS} onChange={setC} />
        <p className="pnote">
          {Number.isFinite(c) && <>Cuantía anual C = m · c = {fmtEur(m * c)} €.</>}
          {m > 1 && <> Cada plazo se descuenta con v<sup>1/{m}</sup>.</>}
        </p>
      </div>
      <InteresRecargo id="r" iS={iS} setI={setI} aS={aS} setA={setA} Field={Field} />
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
  const SC = () => <>C · <S /></>;
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

        <PrimaCard P={D.prima} Z="Y" />
        <MomentosCard momentos={D.momentos} Sym={SC} />
        <MetricasCard M={M} Z="Y" />
        <DistCharts rows={D.rows} M={M} logp={logp} setLogp={setLogp} SegCtl={SegCtl} Z="Y" />

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


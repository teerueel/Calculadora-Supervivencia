/* Pestaña «Seguros de vida». Controles comunes de App.jsx por props; piezas compartidas con
   rentas en comun.jsx; motor en seguros.js. */
import React, { useMemo, useState } from "react";
import { TABLES } from "./data.js";
import { isPer, cohortOf } from "./engine.js";
import { W, TIPOS, NOMBRES, CON_FALLECIMIENTO, CON_SUPERVIVENCIA, CON_DIFERIMIENTO, CON_DURACION, validar, validarTabla, calcular } from "./seguros.js";
import { validarRecargo } from "./distribucion.js";
import { parseNum, parseOrdenes, ERR_ORDENES, fmtA, fmtEur, fmtN, DistCharts, PrimaCard, MomentosCard, MetricasCard, InteresRecargo, TT_TXT } from "./comun.jsx";

/* ============================ Notación ============================ */
/* m|A^1_{x:n⌉}: «1» sobre x (temporal), sobre n (capital diferido) o sin él (vida entera, mixto) */
export function ASym({ m, x, n, uno }) {
  return (
    <span className="sym rsym-a">
      {m && m !== "0" && <sub className="pre">{m}|</sub>}
      <span className="base">A</span>
      <span className="rs-ss">
        <span className="rs-sup" style={{ textAlign: uno === "n" ? "right" : "left" }}>{uno ? "1" : " "}</span>
        <span className="rs-sub">{x}{n != null && <>:<span className="ang">{n}</span></>}</span>
      </span>
    </span>
  );
}

function SymContrato({ tipo, m, x, n }) {
  if (tipo === "temporal") return <ASym m={m} x={x} n={n} uno="x" />;
  if (tipo === "vida_entera") return <ASym m={m} x={x} />;
  if (tipo === "capital_diferido") return <ASym x={x} n={n} uno="n" />;
  return <ASym m={m} x={x} n={n} />;
}

/* Junta tramos de ≥ 3 años consecutivos de fallecimiento: Σ_{j=a}^{a+k−1} _{j|}qₓ = _{a|k}qₓ */
function compactar(psym) {
  const out = [];
  for (const t of psym) {
    const u = out[out.length - 1];
    if (t[0] === "dq" && u && (u[0] === "dq" || u[0] === "dqk") && (u[0] === "dq" ? u[1] + 1 : u[1] + u[2]) === t[1])
      out[out.length - 1] = ["dqk", u[1], (u[0] === "dq" ? 1 : u[2]) + 1];
    else out.push(t);
  }
  return out.flatMap((t) => (t[0] === "dqk" && t[2] < 3 ? Array.from({ length: t[2] }, (_, j) => ["dq", t[1] + j]) : [t]));
}

function Term({ t, x, Sym }) {
  if (t[0] === "dqk") return <Sym pre={`${t[1]}|${t[2]}`} base="q" post={x} />;
  if (t[0] === "dq") return t[1] === 0 ? <Sym base="q" post={x} /> : <Sym pre={`${t[1]}|`} base="q" post={x} />;
  return <Sym pre={String(t[1])} base={t[0]} post={x} />;
}

const NOTAS = {
  temporal: "Paga C al final del año de fallecimiento si (x) fallece entre las edades x + m y x + m + n.",
  vida_entera: "Paga C al final del año de fallecimiento si (x) fallece después de la edad x + m.",
  capital_diferido: "Paga C en t = n si (x) sigue vivo a la edad x + n.",
  mixto: "Paga C_f al final del año de fallecimiento si (x) fallece entre x + m y x + m + n, o C_s en t = m + n si sobrevive.",
};

/* ============================ Pestaña ============================ */
export default function Seguros({ ui }) {
  const { Sym, SegCtl, Field, TableSelect, TableTags } = ui;
  const [key, setKey] = useState("pasem_gen_2");
  const [sex, setSex] = useState("H");
  const [yearS, setYear] = useState("2026");
  const [xS, setX] = useState("45");
  const [tipo, setTipo] = useState("temporal");
  const [nS, setN] = useState("20");
  const [mS, setM] = useState("0");
  const [cfS, setCf] = useState("100000");
  const [csS, setCs] = useState("100000");
  const [iS, setI] = useState(TT_TXT);
  const [aS, setA] = useState("0");
  const [oS, setO] = useState("1, 2, 3");
  const [showD, setShowD] = useState(false);
  const [logp, setLogp] = useState("log");

  const per = isPer(key), mixto = tipo === "mixto";
  const hasF = CON_FALLECIMIENTO.includes(tipo), hasS = CON_SUPERVIVENCIA.includes(tipo);
  const x = parseNum(xS), n = parseNum(nS), m = parseNum(mS), year = parseNum(yearS);
  const Cf = parseNum(cfS), Cs = mixto ? parseNum(csS) : parseNum(cfS); // fuera del mixto, un único capital C
  const I = parseNum(iS) / 100, alpha = parseNum(aS) / 100;
  const ordenes = parseOrdenes(oS);
  let err = validar({ tipo, x, n, m, I, Cf, Cs, needYear: per, year });
  if (!err) err = validarTabla({ key, sex, year: per ? Math.round(year) : 2019, x });
  if (!err) err = validarRecargo(alpha);
  if (!err && !ordenes) err = ERR_ORDENES;

  const D = useMemo(() => (err ? null : calcular({ key, sex, year: per ? Math.round(year) : 2019, tipo, x, n, m, I, Cf, Cs, ordenes, alpha })),
    [err, key, sex, per, year, tipo, x, n, m, I, Cf, Cs, oS, alpha]); // eslint-disable-line react-hooks/exhaustive-deps

  const M = D && D.metricas;
  const xs = D ? fmtA(D.x) : "x", ns = D ? fmtA(D.n) : "n", ms = D ? fmtA(D.m) : "m";
  const CapF = mixto ? <>C<sub>f</sub></> : "C", CapS = mixto ? <>C<sub>s</sub></> : "C";
  const nota = mixto ? NOTAS.mixto : NOTAS[tipo];

  const panel = (
    <aside className="panel" aria-label="Parámetros">
      <div className="block">
        <h2 className="ptitle">Tabla</h2>
        <div className="field"><label htmlFor="s-tabla">Tabla de mortalidad</label><TableSelect id="s-tabla" value={key} onChange={setKey} /></div>
        <TableTags k={key} />
      </div>
      <div className="block">
        <h2 className="ptitle">Asegurado</h2>
        <div className="field"><span className="flabel">Sexo</span><SegCtl label="Sexo" value={sex} onChange={setSex} options={[["H", "Hombre"], ["M", "Mujer"]]} /></div>
        <div className="grid2">
          <Field id="s-x" label="Edad x" value={xS} onChange={setX} />
          {per && <Field id="s-y" label="Año de cálculo" value={yearS} onChange={setYear} />}
        </div>
        <p className="pnote">{per && Number.isFinite(x) && Number.isFinite(year) ? `Generación ${cohortOf(year, x)}.` : "Tabla estática: no depende del año (base 2019)."}</p>
      </div>
      <div className="block">
        <h2 className="ptitle">Contrato</h2>
        <div className="field">
          <label htmlFor="s-tipo">Tipo de seguro</label>
          <select id="s-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>{TIPOS.map((t) => <option key={t} value={t}>{NOMBRES[t]}</option>)}</select>
        </div>
        <div className="grid2">
          {CON_DURACION.includes(tipo) && <Field id="s-n" label="Duración n (años)" value={nS} onChange={setN} />}
          {CON_DIFERIMIENTO.includes(tipo) && <Field id="s-m" label="Diferimiento m (años)" value={mS} onChange={setM} />}
        </div>
        <p className="pnote">{nota}</p>
        <p className="pnote">
          x, n y m enteros. El capital de fallecimiento se paga al final del año de fallecimiento.
          {tipo === "vida_entera" && <> Vida entera: n = w + 1 − x − m{D ? ` = ${ns} años` : ""} (w = {W}).</>}
        </p>
      </div>
      <div className="block">
        <h2 className="ptitle">Capitales</h2>
        {mixto ? (
          <div className="grid2">
            <Field id="s-cf" label="Fallecimiento C_f (€)" value={cfS} onChange={setCf} />
            <Field id="s-cs" label="Supervivencia C_s (€)" value={csS} onChange={setCs} />
          </div>
        ) : <Field id="s-cf" label={`Capital de ${hasS ? "supervivencia" : "fallecimiento"} C (€)`} value={cfS} onChange={setCf} />}
      </div>
      <InteresRecargo id="s" iS={iS} setI={setI} aS={aS} setA={setA} Field={Field} />
      <div className="block">
        <h2 className="ptitle">Momentos</h2>
        <Field id="s-o" label="Órdenes s" value={oS} onChange={setO} />
        <p className="pnote">Lista o rango de enteros entre 1 y 12, p. ej. «1, 2, 3» o «1-4».</p>
      </div>
    </aside>
  );

  if (err) return <div className="layout">{panel}<main className="main"><div className="error" role="alert">{err}</div></main></div>;

  const S = () => <SymContrato tipo={tipo} m={ms} x={xs} n={ns} />;
  const Zs = () => "Z";
  let acc = 0;
  const F = D.rows.map((r) => (acc += r.prob));
  const capOf = (e) => (e.cap === "f" ? CapF : CapS);
  const comp = D.componentes;

  return (
    <div className="layout">
      {panel}
      <main className="main">
        <p className="context">
          {sex === "H" ? "Hombre" : "Mujer"} de {xs} años, {TABLES[key].label}.{" "}
          {per ? `Generación ${D.cohort}, año de cálculo ${Math.round(year)}. ` : "Tabla estática, año base 2019. "}
          Seguro {NOMBRES[tipo].toLowerCase()}{CON_DURACION.includes(tipo) ? ` a ${ns} años` : ""}{D.m > 0 ? `, diferido ${ms} años` : ""}
          {mixto ? `: ${fmtEur(Cf)} € por fallecimiento y ${fmtEur(Cs)} € por supervivencia.` : `: capital de ${fmtEur(Cf)} €.`}
        </p>

        <section className="card results">
          <div className="rrow rhead" style={{ "--accent": "var(--ink)" }}>
            <div className="rsym rsym-big">{mixto ? <S /> : <><span className="rs-c">{fmtEur(Cf)} · </span><S /></>}</div>
            <div className="rtext"><p className="rdesc">Prima pura única: E[Z], con Z el valor actual de la prestación</p></div>
            <div className="rval">
              <span className="rnum">{fmtEur(M.media)} €</span>
              <span className="rpct">Prob. de que se pague el capital: {fmtN(D.pPago)}</span>
            </div>
          </div>
          {mixto && (<>
            <div className="rrow" style={{ "--accent": "var(--death)" }}>
              <div className="rsym" style={{ fontSize: 24 }}><ASym m={ms} x={xs} n={ns} uno="x" /></div>
              <div className="rtext"><p className="rdesc">Parte de fallecimiento: C<sub>f</sub> · <ASym m={ms} x={xs} n={ns} uno="x" /></p></div>
              <div className="rval"><span className="rnum" style={{ fontSize: 20 }}>{fmtEur(comp.fallecimiento)} €</span></div>
            </div>
            <div className="rrow" style={{ "--accent": "var(--surv)" }}>
              <div className="rsym" style={{ fontSize: 24 }}><ASym x={xs} n={fmtA(D.m + D.n)} uno="n" /></div>
              <div className="rtext"><p className="rdesc">Parte de supervivencia: C<sub>s</sub> · <Sym pre={fmtA(D.m + D.n)} base="E" post={xs} /></p></div>
              <div className="rval"><span className="rnum" style={{ fontSize: 20 }}>{fmtEur(comp.supervivencia)} €</span></div>
            </div>
          </>)}
        </section>

        <PrimaCard P={D.prima} Z="Z" />
        <MomentosCard momentos={D.momentos} Sym={Zs} />
        <MetricasCard M={M} Z="Z" />
        <DistCharts rows={D.rows} M={M} logp={logp} setLogp={setLogp} SegCtl={SegCtl} Z="Z" />

        <section className="card">
          <button type="button" className="ghost" aria-expanded={showD} onClick={() => setShowD((s) => !s)}>
            {showD ? "Ocultar" : "Mostrar"} la distribución ({D.rows.length} valores)
          </button>
          {showD && (
            <div className="tablewrap"><table className="ltab rtab">
              <thead><tr>{["Pago en t", "Valor", "Probabilidad", "Valor (€)", "Prob.", "F(z)"].map((t, i) => <th key={t} className={i === 1 || i === 2 ? "l" : ""}>{t}</th>)}</tr></thead>
              <tbody>{D.rows.map((r, i) => {
                const pag = r.eventos.filter((e) => e.cap !== null);
                const ts = [...new Set(pag.map((e) => e.t))], largo = pag.length > 3;
                return (
                  <tr key={i}>
                    <td>{!pag.length ? "—" : largo ? `${ts[0]}…${ts[ts.length - 1]}` : ts.join(", ")}</td>
                    <td className="l rcell">{!pag.length ? "0" : largo ? <>{capOf(pag[0])} · v<sup>t</sup>, t = {ts[0]}…{ts[ts.length - 1]}</>
                      : pag.map((e, j) => <span key={j}>{j > 0 && " = "}{capOf(e)} · v<sup>{e.t}</sup></span>)}</td>
                    <td className="l rcell">{compactar(r.eventos.flatMap((e) => e.psym)).map((t, j) => <span key={j}>{j > 0 && " + "}<Term t={t} x={xs} Sym={Sym} /></span>)}</td>
                    <td>{fmtEur(r.val)}</td><td>{fmtN(r.prob, 8)}</td><td>{fmtN(F[i], 8)}</td>
                  </tr>
                );
              })}</tbody>
            </table></div>
          )}
        </section>
      </main>
    </div>
  );
}

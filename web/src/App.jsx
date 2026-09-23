import React, { useEffect, useMemo, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceArea, ReferenceLine, ReferenceDot, ResponsiveContainer,
} from "recharts";
import { TABLES, TABLE_GROUPS } from "./data.js";
import {
  OMEGA, isPer, tableModel, paramModel, results, curveData, lAt, MODELS, MODEL_KEYS, MODEL_FAMILIES, allDefaults, defaultParams, cohortOf,
} from "./engine.js";
import Atlas, { PARAM_ATLAS } from "./atlas.jsx";

/* ============================ Formato ============================ */
const parseNum = (s) => { const t = String(s).trim().replace(/\s/g, "").replace(",", "."); return /^[-+]?(\d+\.?\d*|\.\d+)(e[-+]?\d+)?$/i.test(t) ? Number(t) : NaN; };
const fmtP = (v) => (Number.isFinite(v) ? v.toLocaleString("es-ES", { minimumFractionDigits: 6, maximumFractionDigits: 6 }) : "—");
const fmtPct = (v) => (Number.isFinite(v) ? (v * 100).toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " %" : "—");
const fmtL = (v) => (Number.isFinite(v) ? v.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—");
const fmtA = (v) => v.toLocaleString("es-ES", { maximumFractionDigits: 4, useGrouping: false });
const fmtE = (v) => (Number.isFinite(v) ? v.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—");
const fmtD = (v, d = 6) => (Number.isFinite(v) ? v.toLocaleString("es-ES", { minimumFractionDigits: d, maximumFractionDigits: d, signDisplay: "always" }) : "—");
const SUP = { "-": "⁻", 0: "⁰", 1: "¹", 2: "²", 3: "³", 4: "⁴", 5: "⁵", 6: "⁶", 7: "⁷", 8: "⁸", 9: "⁹" };
const pow10 = (e) => (e === 0 ? "1" : e === 1 ? "10" : "10" + String(e).split("").map((c) => SUP[c]).join(""));
const fmtParam = (v) => {
  if (v === 0) return "0";
  const a = Math.abs(v);
  if (a >= 1e-3 && a < 1e5) return v.toLocaleString("es-ES", { maximumSignificantDigits: 5 });
  const e = Math.floor(Math.log10(a)), mant = v / 10 ** e;
  return mant.toLocaleString("es-ES", { maximumSignificantDigits: 4 }) + "·" + pow10(e);
};
const I = ({ children }) => <i className="sym-i">{children}</i>;
const isInt = (v) => Math.abs(v - Math.round(v)) < 1e-9;

/* ============================ Tema ============================ */
const LIGHT = { ink: "#1B2A38", muted: "#5B6B7A", rule: "#D9E0E6", sheet: "#FFFFFF", surv: "#1F7A6D", death: "#A8323E", defer: "#C98A1B", mu: "#3C5A8A", ref: "#8A96A3",
  series: ["#1B2A38", "#1F7A6D", "#A8323E", "#C98A1B", "#3C5A8A", "#7B4F8E", "#5E7D2A", "#2A9DB5"] };
const DARK = { ink: "#E4EAF0", muted: "#9AA9B6", rule: "#2D3A46", sheet: "#1A242D", surv: "#4FB3A3", death: "#E0707B", defer: "#E0A94A", mu: "#8FB0E3", ref: "#6E7C89",
  series: ["#E4EAF0", "#4FB3A3", "#E0707B", "#E0A94A", "#8FB0E3", "#B58BC7", "#9CC06A", "#5CC3D6"] };
const isDark = () => {
  if (typeof document === "undefined") return false;
  const a = document.documentElement.getAttribute("data-theme");
  if (a === "dark") return true;
  if (a === "light") return false;
  return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
};
function useTheme() {
  const [d, setD] = useState(isDark);
  useEffect(() => {
    const f = () => setD(isDark());
    const mq = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
    mq && mq.addEventListener && mq.addEventListener("change", f);
    const mo = new MutationObserver(f);
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => { mq && mq.removeEventListener && mq.removeEventListener("change", f); mo.disconnect(); };
  }, []);
  return d ? DARK : LIGHT;
}

/* ============================ Notación ============================ */
function Sym({ pre, base, post }) {
  return (
    <span className="sym">
      {pre !== undefined && <sub className="pre">{pre}</sub>}
      <span className="base">{base}</span>
      {post !== undefined && <sub>{post}</sub>}
    </span>
  );
}
const L = ({ a }) => <Sym base="l" post={typeof a === "number" ? fmtA(a) : a} />;

/* ============================ Controles ============================ */
function SegCtl({ options, value, onChange, small, label }) {
  return (
    <div className={"seg-ctl" + (small ? " small" : "")} role="group" aria-label={label}>
      {options.map(([v, t]) => (
        <button key={v} type="button" aria-pressed={value === v} className={value === v ? "on" : ""} onClick={() => onChange(v)}>{t}</button>
      ))}
    </div>
  );
}

function Field({ id, label, value, onChange, hint }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input id={id} type="text" inputMode="decimal" value={value} onChange={(e) => onChange(e.target.value)} />
      {hint && <span className="hint">{hint}</span>}
    </div>
  );
}

function ParamSlider({ def, value, onChange, idp }) {
  const { min, max } = def, log = def.scale === "log";
  const toU = (v) => (log ? (Math.log(Math.max(v, min)) - Math.log(min)) / (Math.log(max) - Math.log(min)) : (v - min) / (max - min));
  const fromU = (u) => (log ? Math.exp(Math.log(min) + u * (Math.log(max) - Math.log(min))) : min + u * (max - min));
  const [txt, setTxt] = useState(fmtParam(value));
  useEffect(() => { setTxt((cur) => (parseNum(cur) === value ? cur : fmtParam(value))); }, [value]);
  const parsed = parseNum(txt.replace("·10", "e").replace(/[⁻⁰¹²³⁴⁵⁶⁷⁸⁹]/g, (c) => ({ "⁻": "-", "⁰": 0, "¹": 1, "²": 2, "³": 3, "⁴": 4, "⁵": 5, "⁶": 6, "⁷": 7, "⁸": 8, "⁹": 9 })[c]));
  const bad = !(Number.isFinite(parsed) && parsed >= min && parsed <= max);
  const id = `${idp}-${def.k}`;
  return (
    <div className="param">
      <div className="param-head">
        <label htmlFor={id}><span className="psym">{def.sym}</span><span className="pdesc">{def.desc}</span></label>
        <input className="pnum" type="text" inputMode="decimal" value={txt} aria-label={`Valor de ${def.sym}`} aria-invalid={bad}
          onChange={(e) => { setTxt(e.target.value); const v = parseNum(e.target.value.replace("·10", "e")); if (Number.isFinite(v) && v >= min && v <= max) onChange(v); }}
          onBlur={() => bad && setTxt(fmtParam(value))} />
      </div>
      <input id={id} type="range" min={0} max={1000} step={1} value={Math.round(Math.min(1, Math.max(0, toU(value))) * 1000)}
        onChange={(e) => onChange(Number(fromU(+e.target.value / 1000).toPrecision(5)))} />
      <div className="prange"><span>{fmtParam(min)}</span>{log && <span>escala logarítmica</span>}<span>{fmtParam(max)}</span></div>
      {bad && <p className="perr" role="alert">Introduce un valor entre {fmtParam(min)} y {fmtParam(max)}.</p>}
    </div>
  );
}

function TableSelect({ id, value, onChange }) {
  return (
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)}>
      {TABLE_GROUPS.map(([g, keys]) => (
        <optgroup key={g} label={g}>{keys.map((k) => <option key={k} value={k}>{TABLES[k].label}</option>)}</optgroup>
      ))}
    </select>
  );
}

function TableTags({ k }) {
  const t = TABLES[k];
  return (
    <div className="tags">
      <span className={"tag " + (t.kind === "per" ? "t-gen" : "t-est")}>{t.kind === "per" ? "Generacional" : "Estática"}</span>
      <span className={"tag t-" + t.uso}>{t.uso === "supervivencia" ? "Supervivencia" : t.uso === "riesgo" ? "Riesgo" : "Decesos"}</span>
      <span className="tag">{t.orden === 2 ? "2º orden" : "1er orden"}</span>
      <span className="tag">Base {t.base}</span>
    </div>
  );
}

function ResultRow({ accent, sym, desc, value }) {
  return (
    <div className="rrow" style={{ "--accent": accent }}>
      <div className="rsym">{sym}</div>
      <div className="rtext"><p className="rdesc">{desc}</p></div>
      <div className="rval"><span className="rnum">{fmtP(value)}</span><span className="rpct">{fmtPct(value)}</span></div>
    </div>
  );
}

/* ============================ Gráficas ============================ */
function ChartTrio({ series, x, n, m, t, logMu, setLogMu, C, single }) {
  const maxT = OMEGA - x;
  const rows = useMemo(() => {
    if (!series.length) return [];
    return series[0].data.map((d, i) => {
      const r = { t: d.t };
      series.forEach((s) => {
        const e = s.data[i] || {};
        r[s.id + "_S"] = e.S; r[s.id + "_F"] = e.F;
        const mu = e.mu;
        r[s.id + "_mu"] = mu == null || !(mu > 0) ? null : mu;
      });
      return r;
    });
  }, [series]);
  const muDom = useMemo(() => {
    let lo = Infinity, hi = 0;
    rows.forEach((r) => series.forEach((s) => { const v = r[s.id + "_mu"]; if (v > 0 && x + r.t <= 110) { lo = Math.min(lo, v); hi = Math.max(hi, v); } }));
    if (!Number.isFinite(lo)) { lo = 1e-4; hi = 1; }
    hi = Math.min(hi, 10);
    if (logMu) {
      const a = Math.floor(Math.log10(lo)), b = Math.max(a + 1, Math.ceil(Math.log10(hi)));
      return { domain: [10 ** a, 10 ** b], ticks: Array.from({ length: b - a + 1 }, (_, i) => 10 ** (a + i)) };
    }
    return { domain: [0, hi * 1.08], ticks: undefined };
  }, [rows, series, logMu, x]);

  const marks = (
    <>
      {n + m > 0 && m < maxT && <ReferenceArea x1={Math.min(m, maxT)} x2={Math.min(m + n, maxT)} fill={C.defer} fillOpacity={0.13} stroke="none" ifOverflow="hidden" />}
      {n <= maxT && <ReferenceLine x={n} stroke={C.surv} strokeDasharray="4 3" />}
    </>
  );
  const xAxis = (
    <XAxis dataKey="t" type="number" domain={[0, maxT]} allowDecimals tick={{ fill: C.muted, fontSize: 11.5 }}
      tickFormatter={(v) => v.toLocaleString("es-ES")} label={{ value: "t (años)", position: "insideBottom", offset: -12, fill: C.muted, fontSize: 11.5 }} />
  );
  const grid = <CartesianGrid stroke={C.rule} strokeDasharray="2 4" />;
  const tip = (
    <Tooltip formatter={(v, name) => [Number.isFinite(v) ? fmtP(v) : "—", name]} labelFormatter={(tt) => `t = ${fmtA(tt)} (edad ${fmtA(x + tt)})`}
      contentStyle={{ background: C.sheet, border: `1px solid ${C.rule}`, borderRadius: 6, fontSize: 12.5, color: C.ink }} itemSorter={(it) => -it.value} />
  );
  const col = (s, fn) => (single && s.primary ? { S: C.surv, F: C.death, mu: C.mu }[fn] : s.color);
  const lines = (fn) => series.map((s) => (
    <Line key={s.id} type="linear" dataKey={`${s.id}_${fn}`} name={s.label} stroke={col(s, fn)} strokeWidth={s.dash ? 1.6 : 2}
      strokeDasharray={s.dash ? "5 4" : undefined} dot={false} isAnimationActive={false} connectNulls={false} />
  ));
  const tIn = t !== undefined && Number.isFinite(t) && t <= maxT;
  const primary = series.find((s) => s.primary);
  const tVal = tIn && primary ? primary.tVal : undefined;
  const margin = { top: 8, right: 12, bottom: 22, left: 2 };
  const yProb = <YAxis domain={[0, 1]} tickFormatter={(v) => v.toLocaleString("es-ES")} tick={{ fill: C.muted, fontSize: 11.5 }} width={36} />;
  const ariaBase = series.map((s) => s.label).join(", ");

  return (
    <div className="charts">
      <figure className="chart">
        <figcaption>Supervivencia <Sym pre="t" base="p" post="x" /></figcaption>
        <div role="img" aria-label={`Función de supervivencia t p x para ${ariaBase}, desde t = 0 hasta ${fmtA(maxT)}`}>
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={rows} margin={margin}>{grid}{xAxis}{yProb}{marks}{tip}{lines("S")}
              {tVal !== undefined && <ReferenceDot x={t} y={tVal} r={4.5} fill={C.ink} stroke={C.sheet} />}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </figure>
      <figure className="chart">
        <figcaption>Distribución <Sym pre="t" base="q" post="x" /></figcaption>
        <div role="img" aria-label={`Función de distribución t q x para ${ariaBase}`}>
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={rows} margin={margin}>{grid}{xAxis}{yProb}{marks}{tip}{lines("F")}</LineChart>
          </ResponsiveContainer>
        </div>
      </figure>
      <figure className="chart">
        <figcaption className="fc-row">
          <span>Tanto instantáneo <Sym base="μ" post="x+t" /></span>
          <SegCtl small label="Escala del tanto instantáneo" value={logMu ? "log" : "lin"} onChange={(v) => setLogMu(v === "log")} options={[["log", "Log"], ["lin", "Lineal"]]} />
        </figcaption>
        <div role="img" aria-label={`Tanto instantáneo de mortalidad para ${ariaBase}, escala ${logMu ? "logarítmica" : "lineal"}`}>
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={rows} margin={margin}>{grid}{xAxis}
              <YAxis scale={logMu ? "log" : "linear"} domain={muDom.domain} ticks={muDom.ticks} allowDataOverflow
                tickFormatter={(v) => (logMu ? pow10(Math.round(Math.log10(v))) : v.toLocaleString("es-ES", { maximumSignificantDigits: 3 }))}
                tick={{ fill: C.muted, fontSize: 11.5 }} width={44} />
              {n <= maxT && <ReferenceLine x={n} stroke={C.surv} strokeDasharray="4 3" />}
              {tip}{lines("mu")}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </figure>
    </div>
  );
}

/* ============================ Validación ============================ */
function validate({ x, n, m, year, needYear }) {
  if (!Number.isFinite(x) || x < 0 || x > 120) return "La edad x debe ser un número entre 0 y 120.";
  if (!Number.isFinite(n) || n < 0) return "El plazo n debe ser un número mayor o igual que 0.";
  if (!Number.isFinite(m) || m < 0) return "El diferimiento m debe ser un número mayor o igual que 0.";
  if (needYear && (!Number.isInteger(year) || year < 1900 || year > 2200)) return "El año de cálculo debe ser un entero entre 1900 y 2200.";
  return null;
}

/* ============================ Aplicación ============================ */
export default function App() {
  const C = useTheme();
  const [tab, setTab] = useState("tablas");

  // Parámetros compartidos
  const [sex, setSex] = useState("H");
  const [xs, setX] = useState("45"); const [ns, setN] = useState("10"); const [ms, setM] = useState("5");
  const [ys, setY] = useState("2026");
  const [metodo, setMetodo] = useState("lin");
  const [logMu, setLogMu] = useState(true);

  // Tablas
  const [table, setTable] = useState("per_ind_2");
  const [showL, setShowL] = useState(false);

  // Paramétricos
  const [model, setModel] = useState("gompertz");
  const [params, setParams] = useState(allDefaults);
  const [showRef, setShowRef] = useState(true);

  // Comparación
  const [scen, setScen] = useState([
    { id: 1, src: "t:per_ind_2", sex: "H" }, { id: 2, src: "t:pasem_gen_2", sex: "H" },
    { id: 3, src: "m:gompertz", sex: "H", p: defaultParams("gompertz", "H") },
    { id: 4, src: "m:heligman_pollard", sex: "H", p: defaultParams("heligman_pollard", "H") },
  ]);
  const [openScen, setOpenScen] = useState(null);
  const [addSrc, setAddSrc] = useState("m:makeham");

  const x = parseNum(xs), n = parseNum(ns), m = parseNum(ms), year = parseNum(ys);

  /* ---------- Tablas ---------- */
  const tErr = validate({ x, n, m, year, needYear: isPer(table) });
  const tM = useMemo(() => (tErr ? null : tableModel(table, sex, year, x, metodo)), [tErr, table, sex, year, x, metodo]);
  const tR = useMemo(() => (tM ? results(tM, x, n, m) : null), [tM, x, n, m]);
  const lx0 = (R) => R && !(R.lx > 0) ? `lₓ = 0: nadie llega a la edad ${fmtA(x)} con esta ley de mortalidad, así que las probabilidades no están definidas. Elige una edad menor.` : null;
  const tErr2 = tErr || lx0(tR);
  const tCurve = useMemo(() => (tM ? curveData(tM, x) : []), [tM, x]);

  /* ---------- Paramétricos ---------- */
  const pDef = MODELS[model];
  const pVals = params[model][sex];
  const pErr = validate({ x, n, m });
  const pM = useMemo(() => (pErr ? null : paramModel(model, pVals, metodo)), [pErr, model, pVals, metodo]);
  const pR = useMemo(() => (pM ? results(pM, x, n, m) : null), [pM, x, n, m]);
  const pErr2 = pErr || lx0(pR);
  const pCurve = useMemo(() => (pM ? curveData(pM, x) : []), [pM, x]);
  const refCurve = useMemo(() => (pErr || !showRef ? null : curveData(tableModel("pasem_gen_2", sex, 2019, x, metodo), x)), [pErr, showRef, sex, x, metodo]);
  const setParam = (k, v) => setParams((cur) => ({ ...cur, [model]: { ...cur[model], [sex]: { ...cur[model][sex], [k]: v } } }));
  const resetParams = () => setParams((cur) => ({ ...cur, [model]: { ...cur[model], [sex]: defaultParams(model, sex) } }));

  /* ---------- Comparación ---------- */
  const cNeedYear = scen.some((s) => s.src.startsWith("t:") && isPer(s.src.slice(2)));
  const cErr = validate({ x, n, m, year, needYear: cNeedYear });
  const scenName = (s) => {
    const k = s.src.slice(2);
    const base = s.src.startsWith("t:") ? TABLES[k].short : MODELS[k].name;
    const same = scen.filter((c) => c.src === s.src);
    return same.length > 1 ? `${base} (${same.indexOf(s) + 1})` : base;
  };
  const scenLabel = (s) => scenName(s) + (s.sex === "H" ? ", hombre" : ", mujer");
  const cData = useMemo(() => {
    if (cErr) return [];
    return scen.map((s, i) => {
      const k = s.src.slice(2);
      const M = s.src.startsWith("t:") ? tableModel(k, s.sex, year, x, metodo) : paramModel(k, s.p, metodo);
      return { ...s, label: scenLabel(s), color: C.series[i % C.series.length], r: results(M, x, n, m), data: curveData(M, x) };
    });
  }, [cErr, scen, year, x, n, m, metodo, C]);
  const updScen = (id, fn) => setScen((cur) => cur.map((c) => (c.id === id ? fn(c) : c)));
  const setScenSex = (s, v) => updScen(s.id, (c) => (c.src.startsWith("m:") ? { ...c, sex: v, p: { ...params[c.src.slice(2)][v] } } : { ...c, sex: v }));
  const addScen = () => setScen((cur) => {
    const id = Math.max(0, ...cur.map((c) => c.id)) + 1;
    const k = addSrc.slice(2);
    if (addSrc.startsWith("m:")) setOpenScen(id);
    return [...cur, addSrc.startsWith("m:") ? { id, src: addSrc, sex, p: { ...params[k][sex] } } : { id, src: addSrc, sex }];
  });

  const needInterp = !isInt(x) || !isInt(n) || !isInt(m);
  const horizonBlock = () => (
    <div className="block">
      <h2 className="ptitle">Edad y horizonte</h2>
      <div className="grid2">
        <Field id={"x-" + tab} label="Edad x" value={xs} onChange={setX} />
        <Field id={"n-" + tab} label="Plazo n" value={ns} onChange={setN} />
        <Field id={"m-" + tab} label="Diferimiento m" value={ms} onChange={setM} />
      </div>
      <p className="pnote">x, n y m admiten decimales.</p>
    </div>
  );
  const interpBlock = (note) => (
    <div className="block">
      <h2 className="ptitle">Edades no enteras</h2>
      <SegCtl label="Interpolación" value={metodo} onChange={setMetodo} options={[["lin", "Lineal"], ["exp", "Exponencial"]]} />
      <p className="pnote">{note}</p>
    </div>
  );

  const threeRows = (R, sx) => (
    <>
      <ResultRow accent={C.surv} sym={<Sym pre={fmtA(n)} base="p" post={fmtA(x)} />} value={R.npx}
        desc={`Sobrevivir ${fmtA(n)} años, hasta la edad ${fmtA(x + n)}`} />
      <ResultRow accent={C.death} sym={<Sym pre={fmtA(n)} base="q" post={fmtA(x)} />} value={R.nqx}
        desc={`Fallecer antes de la edad ${fmtA(x + n)}`} />
      <ResultRow accent={C.defer} sym={<Sym pre={`${fmtA(m)}|${fmtA(n)}`} base="q" post={fmtA(x)} />} value={R.mnqx}
        desc={`Fallecer entre las edades ${fmtA(x + m)} y ${fmtA(x + m + n)}`} />
      {sx}
    </>
  );

  return (
    <div className="app">
      <header className="head">
        <div className="brand">
          <h1>Calculadora de supervivencia</h1>
          <p>Probabilidades de supervivencia y fallecimiento con las tablas PER2020 y PASEM2020 (BOE-A-2020-17154) y con leyes paramétricas de mortalidad.</p>
        </div>
        <nav className="tabs" role="tablist" aria-label="Secciones">
          {[["tablas", "Tablas de mortalidad"], ["param", "Modelos paramétricos"], ["cmp", "Comparación"], ["atlas", "Atlas"]].map(([k, lbl]) => (
            <button key={k} role="tab" type="button" aria-selected={tab === k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}>{lbl}</button>
          ))}
        </nav>
      </header>

      {tab === "atlas" ? <Atlas /> : (
        <div className="layout">
          {/* ====================== PANEL ====================== */}
          <aside className="panel" aria-label="Parámetros">
            {tab === "tablas" && (<>
              <div className="block">
                <h2 className="ptitle">Tabla</h2>
                <div className="field"><label htmlFor="tabla">Tabla de mortalidad</label><TableSelect id="tabla" value={table} onChange={setTable} /></div>
                <TableTags k={table} />
              </div>
              <div className="block">
                <h2 className="ptitle">Asegurado</h2>
                <div className="field"><span className="flabel">Sexo</span><SegCtl label="Sexo" value={sex} onChange={setSex} options={[["H", "Hombre"], ["M", "Mujer"]]} /></div>
                {isPer(table)
                  ? <Field id="y" label="Año de cálculo" value={ys} onChange={setY} hint={Number.isFinite(x) && Number.isInteger(year) ? `Generación ${cohortOf(year, x)}` : undefined} />
                  : <p className="pnote">Tabla estática: no depende del año (base 2019).</p>}
              </div>
              {horizonBlock()}
              {interpBlock("Se usa cuando x, n o m no son enteros, y define cómo se reparte la mortalidad dentro de cada año.")}
            </>)}

            {tab === "param" && (<>
              <div className="block">
                <h2 className="ptitle">Modelo</h2>
                <div className="field">
                  <label htmlFor="modelo">Ley de mortalidad</label>
                  <select id="modelo" value={model} onChange={(e) => setModel(e.target.value)}>
                    {MODEL_FAMILIES.map((f) => <optgroup key={f} label={f}>{MODEL_KEYS.filter((k) => MODELS[k].family === f).map((k) => <option key={k} value={k}>{MODELS[k].name}</option>)}</optgroup>)}
                  </select>
                </div>
                <p className="mformula">{PARAM_ATLAS[model].mu}</p>
                <div className="field"><span className="flabel">Sexo</span><SegCtl label="Sexo" value={sex} onChange={setSex} options={[["H", "Hombre"], ["M", "Mujer"]]} /></div>
              </div>
              <div className="block">
                <div className="ptitle-row"><h2 className="ptitle">Parámetros</h2><button type="button" className="ghost small" onClick={resetParams}>Restaurar</button></div>
                {pDef.params.map((d) => <ParamSlider key={model + sex + d.k} idp={model + sex} def={d} value={pVals[d.k]} onChange={(v) => setParam(d.k, v)} />)}
                <p className="pnote">Valores iniciales: ajuste por mínimos cuadrados a PASEM2020 General 2º orden ({sex === "H" ? "hombres" : "mujeres"}). No son parámetros publicados.</p>
              </div>
              {horizonBlock()}
              {pDef.kind === "disc"
                ? interpBlock("Heligman–Pollard da qₓ en edades enteras: entre ellas se interpola como en una tabla.")
                : null}
              <div className="block">
                <h2 className="ptitle">Referencia</h2>
                <label className="check"><input type="checkbox" checked={showRef} onChange={(e) => setShowRef(e.target.checked)} /> Superponer PASEM2020 General 2º orden</label>
              </div>
            </>)}

            {tab === "cmp" && (<>
              <div className="block">
                <h2 className="ptitle">Escenarios</h2>
                <ul className="scen">
                  {scen.map((s, i) => {
                    const k = s.src.slice(2), isM = s.src.startsWith("m:"), open = isM && openScen === s.id;
                    const color = C.series[i % C.series.length];
                    const name = scenName(s);
                    return (
                      <li key={s.id} className={open ? "open" : ""}>
                        <div className="srow">
                          <span className="swatch line" style={{ background: color }} />
                          {isM ? (
                            <button type="button" className="sname sbtn" aria-expanded={open} aria-controls={`sp-${s.id}`}
                              onClick={() => setOpenScen(open ? null : s.id)}>
                              <span className="chev" aria-hidden="true">{open ? "▾" : "▸"}</span>{name}
                            </button>
                          ) : <span className="sname">{name}</span>}
                          <SegCtl small label={`Sexo de ${name}`} value={s.sex} onChange={(v) => setScenSex(s, v)} options={[["H", "H"], ["M", "M"]]} />
                          {scen.length > 1 && <button type="button" className="x" aria-label={`Quitar ${name}`}
                            onClick={() => setScen((cur) => cur.filter((c) => c.id !== s.id))}>×</button>}
                        </div>
                        {open && (
                          <div className="sparams" id={`sp-${s.id}`}>
                            <p className="mformula">{PARAM_ATLAS[k].mu}</p>
                            {MODELS[k].params.map((d) => (
                              <ParamSlider key={s.id + s.sex + d.k} idp={`c${s.id}${s.sex}`} def={d} value={s.p[d.k]}
                                onChange={(v) => updScen(s.id, (c) => ({ ...c, p: { ...c.p, [d.k]: v } }))} />
                            ))}
                            <button type="button" className="ghost small" onClick={() => updScen(s.id, (c) => ({ ...c, p: defaultParams(k, c.sex) }))}>Restaurar valores iniciales</button>
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
                {scen.length < 8 && (
                  <div className="addrow">
                    <select aria-label="Escenario a añadir" value={addSrc} onChange={(e) => setAddSrc(e.target.value)}>
                      {TABLE_GROUPS.map(([g, keys]) => <optgroup key={g} label={"Tablas · " + g}>{keys.map((k) => <option key={k} value={"t:" + k}>{TABLES[k].short}</option>)}</optgroup>)}
                      {MODEL_FAMILIES.map((f) => <optgroup key={f} label={"Modelos · " + f}>{MODEL_KEYS.filter((k) => MODELS[k].family === f).map((k) => <option key={k} value={"m:" + k}>{MODELS[k].name}</option>)}</optgroup>)}
                    </select>
                    <button type="button" className="ghost" onClick={addScen}>Añadir</button>
                  </div>
                )}
                <p className="pnote">Pulsa el nombre de un modelo para ajustar sus parámetros aquí mismo. Cada escenario tiene los suyos, así que puedes comparar, por ejemplo, dos Gompertz distintos.</p>
              </div>
              {horizonBlock()}
              <div className="block">
                <h2 className="ptitle">Generación y fraccionamiento</h2>
                {cNeedYear ? <Field id="y-cmp" label="Año de cálculo (PER2020)" value={ys} onChange={setY} /> : <p className="pnote">Ningún escenario es generacional.</p>}
                <div className="field"><span className="flabel">Interpolación entre edades</span>
                  <SegCtl label="Interpolación" value={metodo} onChange={setMetodo} options={[["lin", "Lineal"], ["exp", "Exponencial"]]} /></div>
              </div>
            </>)}
          </aside>

          {/* ====================== RESULTADOS ====================== */}
          <main className="main">
            {tab === "tablas" && (tErr2 ? <div className="error" role="alert">{tErr2}</div> : (<>
              <p className="context">{sex === "H" ? "Hombre" : "Mujer"} de {fmtA(x)} años, {TABLES[table].label}. {isPer(table) ? `Generación ${tM.cohort}, año de cálculo ${year}.` : "Tabla estática, año base 2019."}{needInterp && ` Edades no enteras con interpolación ${metodo === "lin" ? "lineal" : "exponencial"}.`}</p>
              <section className="card results" aria-label="Resultados">
                {threeRows(tR, (
                  <div className="rfoot">
                    Esperanza de vida: abreviada <Sym base="e" post={fmtA(x)} /> = {fmtE(tR.ex)} años; completa <Sym base="e̊" post={fmtA(x)} /> = {fmtE(tR.ecx)} años.
                    {x + m + n > OMEGA && <span className="warn"> x + m + n supera ω = 121, donde <L a="ω" /> = 0.</span>}
                  </div>
                ))}
              </section>
              <ChartTrio C={C} x={x} n={n} m={m} t={n} logMu={logMu} setLogMu={setLogMu} single
                series={[{ id: "a", label: TABLES[table].short, primary: true, data: tCurve, tVal: tR.npx }]} />
              <p className="caption">Línea discontinua y punto en t = {fmtA(n)}; franja ocre entre t = {fmtA(m)} y t = {fmtA(m + n)}. Con interpolación lineal, μ crece dentro de cada año; con la exponencial, es escalonada.</p>
              <section className="card">
                <button type="button" className="ghost" aria-expanded={showL} onClick={() => setShowL((s) => !s)}>{showL ? "Ocultar" : "Mostrar"} la tabla <L a="x" /> utilizada</button>
                {showL && (
                  <div className="tablewrap">
                    <table className="ltab">
                      <thead><tr><th>Edad</th>{isPer(table) && <th>Año</th>}<th>q (‰)</th><th>l</th><th>d</th></tr></thead>
                      <tbody>
                        {Array.from({ length: Math.max(0, Math.min(OMEGA, Math.ceil(x + m + n) + 5) - Math.floor(x) + 1) }, (_, i) => Math.floor(x) + i).map((a) => {
                          const key = [x, x + n, x + m, x + m + n].some((v) => Math.floor(v) === a);
                          return (
                            <tr key={a} className={key ? "mark" : ""}>
                              <td>{a}</td>{isPer(table) && <td>{tM.cohort + a}</td>}
                              <td>{a <= 120 ? (tM.q[a] * 1000).toLocaleString("es-ES", { maximumFractionDigits: 4 }) : "—"}</td>
                              <td>{fmtL(tM.l[a] ?? 0)}</td>
                              <td>{a <= 120 ? fmtL(tM.l[a] - tM.l[a + 1]) : "—"}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </section>
            </>))}

            {tab === "param" && (pErr2 ? <div className="error" role="alert">{pErr2}</div> : (<>
              <p className="context">{pDef.name}, {sex === "H" ? "hombre" : "mujer"} de {fmtA(x)} años. {pDef.kind === "disc" ? "lₓ se construye con las qₓ del modelo." : "lₓ = 100.000 · S(x), con S(x) = e^(−∫μ)."}</p>
              <section className="card results" aria-label="Resultados">
                {threeRows(pR, (
                  <div className="rfoot">
                    Esperanza de vida completa <Sym base="e̊" post={fmtA(x)} /> = {fmtE(pR.ecx)} años{pR.ex !== undefined && <>; abreviada <Sym base="e" post={fmtA(x)} /> = {fmtE(pR.ex)} años</>}.
                  </div>
                ))}
              </section>
              <ChartTrio C={C} x={x} n={n} m={m} t={n} logMu={logMu} setLogMu={setLogMu} single
                series={[{ id: "a", label: pDef.name, primary: true, data: pCurve, tVal: pR.npx },
                  ...(refCurve ? [{ id: "ref", label: "PASEM2020 General 2º", color: C.ref, dash: true, data: refCurve }] : [])]} />
              <p className="caption">Mueve los parámetros y las tres curvas se recalculan al instante.{refCurve && " La línea gris discontinua es la PASEM2020 General 2º orden del mismo sexo."}</p>
            </>))}

            {tab === "cmp" && (cErr ? <div className="error" role="alert">{cErr}</div> : (<>
              <p className="context">{cData.length} escenarios evaluados en la edad {fmtA(x)}, con n = {fmtA(n)} y m = {fmtA(m)}.{cNeedYear && ` Las PER2020 corresponden a la generación ${cohortOf(year, x)}.`}</p>
              <section className="card">
                <div className="tablewrap flat">
                  <table className="cmp">
                    <thead><tr>
                      <th className="l">Escenario</th>
                      <th><Sym pre={fmtA(n)} base="p" post={fmtA(x)} /></th>
                      <th><Sym pre={fmtA(n)} base="q" post={fmtA(x)} /></th>
                      <th><Sym pre={`${fmtA(m)}|${fmtA(n)}`} base="q" post={fmtA(x)} /></th>
                      <th><Sym base="e̊" post={fmtA(x)} /></th>
                    </tr></thead>
                    <tbody>
                      {cData.map((s, i) => {
                        const ref = cData[0].r;
                        const cell = (v, rv, d = 6) => (
                          <td><span className="cv">{d === 6 ? fmtP(v) : fmtE(v)}</span>{i > 0 && <span className="cd">{fmtD(v - rv, d)}</span>}</td>
                        );
                        return (
                          <tr key={s.id}>
                            <td className="l"><span className="mlabel"><span className="swatch" style={{ background: s.color }} />{s.label}{i === 0 && <span className="refbadge">referencia</span>}</span></td>
                            {cell(s.r.npx, ref.npx)}{cell(s.r.nqx, ref.nqx)}{cell(s.r.mnqx, ref.mnqx)}{cell(s.r.ecx, ref.ecx, 2)}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <p className="caption">Debajo de cada valor, la diferencia con el primer escenario.</p>
              </section>
              <ul className="legend">{cData.map((s) => <li key={s.id}><span className="swatch line" style={{ background: s.color }} />{s.label}</li>)}</ul>
              <ChartTrio C={C} x={x} n={n} m={m} logMu={logMu} setLogMu={setLogMu} series={cData} />
            </>))}
          </main>
        </div>
      )}

      <footer className="foot">
        Fuente de las tablas: Resolución de la DGSFP de 17 de diciembre de 2020 (BOE-A-2020-17154), anexos 1.1, 1.2, 1.3 y 2.1. Los valores publicados están redondeados; puede haber diferencias mínimas en el último decimal.
        Los parámetros iniciales de los modelos proceden de un ajuste propio a la PASEM2020 General 2º orden, no de una fuente oficial.
      </footer>
    </div>
  );
}

import React, { useState } from "react";
import { MODELS, MODEL_KEYS, MODEL_FAMILIES, paramModel, defaultParams } from "./engine.js";

/* Pequeños componentes de notación */
const I = ({ children }) => <i>{children}</i>;
const Mth = ({ children }) => <span className="math">{children}</span>;
const S = ({ pre, base, post }) => (
  <span className="sym">{pre !== undefined && <sub className="pre">{pre}</sub>}<span className="base">{base}</span>{post !== undefined && <sub>{post}</sub>}</span>
);
const mu = (a = "x") => <S base="μ" post={a} />;

/* ============================ Atlas paramétrico ============================ */
export const PARAM_ATLAS = {
  exponencial: {
    origin: "Fuerza de mortalidad constante", shape: "Constante", range: "Tramos cortos de edad",
    idea: "El riesgo de fallecer es el mismo a cualquier edad: no hay envejecimiento.",
    mu: <Mth>{mu()} = λ</Mth>,
    uses: ["Hipótesis de fuerza constante entre edades enteras para fraccionar la edad.", "Referencia frente a la que contrastar modelos con envejecimiento.", "Fiabilidad y riesgos sin desgaste en periodos cortos."],
    cons: ["Falta de memoria: la probabilidad de sobrevivir t años no depende de la edad.", "Irreal para la vida humana en horizontes largos.", "La esperanza de vida completa es 1/λ a cualquier edad."],
    related: "Es Weibull con β = 1 y Gompertz con c = 1." },
  demoivre: {
    origin: "Abraham de Moivre, 1725", shape: "Creciente, diverge en ω", range: "Docencia y fraccionamiento",
    idea: "Los supervivientes decrecen linealmente hasta una edad límite ω: los fallecimientos se reparten por igual.",
    mu: <Mth>{mu()} = 1 / (ω − <I>x</I>)</Mth>,
    uses: ["Docencia y cálculo a mano: todo tiene forma cerrada sencilla.", "Fundamento de la hipótesis de distribución uniforme de fallecimientos (UDD) dentro del año.", "Aproximaciones rápidas en tramos cortos."],
    cons: ["Fallecimientos constantes a todas las edades: infancia y edad adulta irreales.", "La fuerza de mortalidad solo crece de forma apreciable muy cerca de ω.", "Obliga a fijar ω desde fuera: ajustado a una tabla real, ω se dispara por encima de 160."],
    related: "Ley de supervivencia uniforme: la base de la hipótesis UDD." },
  gompertz: {
    origin: "Benjamin Gompertz, 1825", shape: "Exponencial creciente", range: "Adultos, 30–90 años",
    idea: "El riesgo de muerte se multiplica por c cada año de edad: log μ crece en línea recta.",
    mu: <Mth>{mu()} = <I>B</I> <I>c</I><sup><I>x</I></sup></Mth>,
    uses: ["Mortalidad adulta humana, en seguros de vida y de rentas.", "Graduación de tablas y extrapolación en edades adultas.", "Punto de partida de Makeham, Perks, Kannisto y Heligman–Pollard."],
    cons: ["Ignora la mortalidad infantil y la joroba de accidentes juvenil.", "Sobreestima la mortalidad a edades muy avanzadas: no se desacelera.", "No incluye mortalidad independiente de la edad."],
    related: "Makeham con A = 0." },
  makeham: {
    origin: "William Makeham, 1860", shape: "Constante más exponencial", range: "Adultos, 20–90 años",
    idea: "Añade a Gompertz un término A de mortalidad accidental, igual a cualquier edad.",
    mu: <Mth>{mu()} = <I>A</I> + <I>B</I> <I>c</I><sup><I>x</I></sup></Mth>,
    uses: ["Graduación clásica de tablas de asegurados.", "Seguros sobre varias vidas: permite sustituir el grupo por una única vida de edad equivalente.", "Primas y reservas con expresiones analíticas."],
    cons: ["El término constante no reproduce la joroba de accidentes de los 18–25 años.", "Hereda la sobreestimación de Gompertz en la vejez extrema.", "A y B están muy correlacionados al estimar."],
    related: "Gompertz si A = 0; Siler le añade un término infantil." },
  weibull: {
    origin: "Waloddi Weibull, 1951", shape: "Potencial: decrece, constante o crece", range: "Fiabilidad y estudios clínicos",
    idea: "La fuerza de mortalidad es una potencia de la edad; la forma β decide si decrece, se mantiene o crece.",
    mu: <Mth>{mu()} = (β/θ)(<I>x</I>/θ)<sup>β−1</sup></Mth>,
    uses: ["Fiabilidad e ingeniería: tiempo hasta el fallo.", "Supervivencia clínica: tiempo desde el diagnóstico o el tratamiento.", "Modelos paramétricos de riesgos proporcionales."],
    cons: ["Crece de forma polinómica: ajusta peor que Gompertz la mortalidad adulta humana.", "En x = 0 la fuerza de mortalidad es infinita si β < 1 y nula si β > 1.", "Siempre monótona: no genera forma de bañera."],
    related: "Exponencial si β = 1." },
  perks: {
    origin: "Wilfred Perks, 1932", shape: "Sigmoide, se estabiliza en B/D", range: "Adultos y edades avanzadas",
    idea: "Versión logística de Makeham: el crecimiento exponencial se frena y μ tiende a la meseta B/D.",
    mu: <Mth>{mu()} = (<I>A</I> + <I>B c</I><sup><I>x</I></sup>) / (1 + <I>D c</I><sup><I>x</I></sup>)</Mth>,
    uses: ["Mortalidad en edades avanzadas con desaceleración (meseta).", "Tablas de rentas vitalicias, donde no conviene sobreestimar la mortalidad en la vejez.", "Se justifica por heterogeneidad: fragilidad gamma sobre Makeham (modelo de Beard)."],
    cons: ["Cuatro parámetros difíciles de identificar con pocos datos en edades altas.", "La meseta la determinan muy pocas observaciones extremas.", "Sin componente infantil ni de accidentes."],
    related: "Makeham si D = 0; Kannisto si A = 0 y B = D." },
  kannisto: {
    origin: "Väinö Kannisto, 1992", shape: "Logístico, tiende a 1", range: "Edades de 80 en adelante",
    idea: "Logística de dos parámetros pensada para cerrar la tabla en edades muy avanzadas, con μ acotada por 1.",
    mu: <Mth>{mu()} = <I>a e</I><sup><I>bx</I></sup> / (1 + <I>a e</I><sup><I>bx</I></sup>)</Mth>,
    uses: ["Suavizado y extrapolación de la mortalidad a partir de los 80 años.", "Método con el que la Human Mortality Database cierra sus tablas en edades altas.", "Estudios de longevidad extrema."],
    cons: ["Solo válido en la vejez: no sirve para una tabla completa.", "Asíntota fija en 1, sin parámetro propio para la meseta.", "Muy sensible a la calidad de los datos en edades extremas."],
    related: "Perks con A = 0 y B = D." },
  thiele: {
    origin: "Thorvald Thiele, 1871", shape: "Bañera con joroba", range: "Todas las edades",
    idea: "Primera ley para toda la vida: término infantil decreciente, joroba juvenil gaussiana y senescencia de Gompertz.",
    mu: <Mth>{mu()} = <I>a</I><sub>1</sub>e<sup>−<I>b</I><sub>1</sub><I>x</I></sup> + <I>a</I><sub>2</sub>e<sup>−½<I>b</I><sub>2</sub>(<I>x</I>−<I>c</I>)²</sup> + <I>a</I><sub>3</sub>e<sup><I>b</I><sub>3</sub><I>x</I></sup></Mth>,
    uses: ["Representar la tabla completa de 0 a 120 años con una única expresión.", "Descomponer la mortalidad por etapas vitales.", "Antecedente directo de Heligman–Pollard."],
    cons: ["Siete parámetros: estimación inestable y muy correlacionada.", "La joroba gaussiana es simétrica; la real sube más deprisa de lo que baja.", "Con la PASEM2020 de mujeres la joroba casi desaparece y el modelo degenera en Siler."],
    related: "Siler si la joroba se sustituye por una constante." },
  siler: {
    origin: "William Siler, 1979", shape: "Bañera", range: "Todas las edades",
    idea: "Tres riesgos en competencia: inmadurez (decreciente), fondo constante y senescencia (Gompertz).",
    mu: <Mth>{mu()} = <I>a</I><sub>1</sub>e<sup>−<I>b</I><sub>1</sub><I>x</I></sup> + <I>a</I><sub>2</sub> + <I>a</I><sub>3</sub>e<sup><I>b</I><sub>3</sub><I>x</I></sup></Mth>,
    uses: ["Curvas en bañera en demografía, ecología y paleodemografía.", "Comparar poblaciones humanas y animales con pocos parámetros.", "Ajustes con datos escasos o edades agrupadas."],
    cons: ["No recoge la joroba de accidentes juvenil.", "Parámetros muy correlacionados, sobre todo a₂ con a₃.", "Hereda la sobreestimación de Gompertz en la vejez extrema."],
    related: "Makeham más un término infantil." },
  heligman_pollard: {
    origin: "Larry Heligman y John Pollard, 1980", shape: "Bañera con joroba", range: "Todas las edades",
    idea: "Modela el cociente q/p con tres sumandos con significado demográfico: infancia, joroba de accidentes y senescencia.",
    mu: <Mth><S base="q" post="x" />/<S base="p" post="x" /> = <I>A</I><sup>(<I>x</I>+<I>B</I>)<sup><I>C</I></sup></sup> + <I>D</I>e<sup>−<I>E</I>(ln <I>x</I> − ln <I>F</I>)²</sup> + <I>G H</I><sup><I>x</I></sup></Mth>,
    uses: ["Graduación de tablas completas en demografía y en el sector asegurador.", "Proyección de la mortalidad modelando la evolución de sus parámetros.", "Interpretación directa: cada parámetro tiene lectura demográfica."],
    cons: ["Ocho parámetros: mínimos locales y dependencia de los valores iniciales.", "Es discreto, sobre qₓ: la fuerza de mortalidad depende de cómo se fraccione la edad.", "La componente senescente sobreestima en edades muy altas."],
    related: "Descendiente de Thiele, con la joroba lognormal en lugar de gaussiana." },
};

function Spark({ k, sex = "H" }) {
  const M = paramModel(k, defaultParams(k, sex), "exp");
  const pts = [];
  for (let a = 0; a <= 110; a += 1) { const v = M.mu(a + 0.5); if (v > 0 && Number.isFinite(v)) pts.push([a, Math.log10(Math.min(v, 10))]); }
  const W = 170, Hh = 58, lo = -5, hi = 1;
  const X = (a) => (a / 110) * W, Y = (v) => Hh - ((Math.max(lo, v) - lo) / (hi - lo)) * Hh;
  const d = pts.map(([a, v], i) => `${i ? "L" : "M"}${X(a).toFixed(1)},${Y(v).toFixed(1)}`).join("");
  return (
    <svg className="spark" viewBox={`0 0 ${W} ${Hh}`} role="img" aria-label={`Forma de la fuerza de mortalidad del modelo ${MODELS[k].name}, escala logarítmica, edades 0 a 110`}>
      {[-4, -2, 0].map((g) => <line key={g} x1="0" x2={W} y1={Y(g)} y2={Y(g)} className="sparkgrid" />)}
      <path d={d} className="sparkline" />
    </svg>
  );
}

function ParamAtlas() {
  return (
    <>
      <p className="lead">Diez leyes de mortalidad, de la más simple a las que describen la vida completa. Cada miniatura dibuja log μ entre 0 y 110 años con los valores iniciales de la calculadora (hombre).</p>
      <section className="card">
        <div className="tablewrap flat">
          <table className="sum">
            <thead><tr><th className="l">Modelo</th><th>Parámetros</th><th className="l">Forma de μ</th><th className="l">Tramo de edades</th><th className="l">Principal limitación</th></tr></thead>
            <tbody>
              {MODEL_KEYS.map((k) => (
                <tr key={k}>
                  <td className="l"><b>{MODELS[k].name}</b><span className="sub">{PARAM_ATLAS[k].origin}</span></td>
                  <td className="c"><span className="bignum">{MODELS[k].params.length}</span></td>
                  <td className="l">{PARAM_ATLAS[k].shape}</td>
                  <td className="l">{PARAM_ATLAS[k].range}</td>
                  <td className="l">{PARAM_ATLAS[k].cons[0]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      {MODEL_FAMILIES.map((fam) => (
        <section key={fam} className="atlas-fam">
          <h3 className="famtitle">{fam}</h3>
          <div className="atlas-grid">
            {MODEL_KEYS.filter((k) => MODELS[k].family === fam).map((k) => {
              const a = PARAM_ATLAS[k];
              return (
                <article key={k} className="acard">
                  <header className="ahead">
                    <div>
                      <h4>{MODELS[k].name}</h4>
                      <p className="aorigin">{a.origin}</p>
                    </div>
                    <div className="acount"><span className="bignum">{MODELS[k].params.length}</span><span className="sub">{MODELS[k].params.length === 1 ? "parámetro" : "parámetros"}</span></div>
                  </header>
                  <Spark k={k} />
                  <p className="aformula">{a.mu}</p>
                  <p className="aidea">{a.idea}</p>
                  <p className="pnames">{MODELS[k].params.map((p) => <span key={p.k}><b className="psym">{p.sym}</b> {p.desc}</span>)}</p>
                  <div className="acols">
                    <div><h5>Casos de uso</h5><ul>{a.uses.map((u, i) => <li key={i}>{u}</li>)}</ul></div>
                    <div><h5>Desventajas</h5><ul>{a.cons.map((u, i) => <li key={i}>{u}</li>)}</ul></div>
                  </div>
                  <p className="arel">{a.related}</p>
                </article>
              );
            })}
          </div>
        </section>
      ))}
    </>
  );
}

/* ============================ Atlas no paramétrico ============================ */
const INTERP_ATLAS = [
  { name: "Lineal (UDD)", inApp: true,
    hyp: "Los fallecimientos del año se reparten uniformemente: lₓ₊ₛ es una recta entre lₓ y lₓ₊₁.",
    f: <Mth><S pre="s" base="p" post="x" /> = 1 − <I>s</I>·<S base="q" post="x" /> &nbsp;&nbsp; {mu("x+s")} = <S base="q" post="x" /> / (1 − <I>s</I>·<S base="q" post="x" />)</Mth>,
    pros: ["La más sencilla de aplicar a mano.", "e̊ₓ = eₓ + ½ de forma exacta.", "Base de las aproximaciones habituales para pagos fraccionados."],
    cons: ["μ crece dentro del año y salta en cada edad entera.", "Con qₓ = 1, μ se dispara al final del último año."],
    uses: "Primas y rentas fraccionadas, edades actuariales no enteras, cálculo a mano." },
  { name: "Exponencial (fuerza constante)", inApp: true,
    hyp: "La fuerza de mortalidad es constante dentro de cada año: lₓ₊ₛ decrece exponencialmente.",
    f: <Mth><S pre="s" base="p" post="x" /> = <S base="p" post="x" /><sup><I>s</I></sup> &nbsp;&nbsp; {mu("x+s")} = −ln <S base="p" post="x" /></Mth>,
    pros: ["Coherente con modelos en tiempo continuo y con la exposición al riesgo.", "Multiplicativa: la supervivencia de varios tramos se encadena sin error.", "Es la hipótesis natural cuando se trabaja con tantos centrales de mortalidad."],
    cons: ["μ es escalonada: constante dentro del año y con saltos en las edades enteras.", "Con qₓ = 1 la supervivencia cae a cero en cuanto empieza el año."],
    uses: "Estimación de tasas a partir de exposición, modelos multiestado, fraccionamiento en valoración continua." },
  { name: "Balducci (hiperbólica)", inApp: false,
    hyp: "La probabilidad de fallecer en el resto del año es proporcional al tiempo que queda: ₁₋ₛqₓ₊ₛ = (1 − s)·qₓ.",
    f: <Mth><S pre="s" base="p" post="x" /> = <S base="p" post="x" /> / (1 − (1 − <I>s</I>)·<S base="q" post="x" />) &nbsp;&nbsp; {mu("x+s")} = <S base="q" post="x" /> / (1 − (1 − <I>s</I>)·<S base="q" post="x" />)</Mth>,
    pros: ["Históricamente cómoda para estimar qₓ a partir de expuestos al riesgo.", "Da expresiones sencillas para las probabilidades del resto del año."],
    cons: ["μ decrece dentro del año: contrario a la mortalidad adulta real.", "Hoy casi no se usa fuera del contexto histórico."],
    uses: "Referencia histórica; no está implementada en la calculadora." },
];

const TABLE_ATLAS = [
  { name: "PER2020 Individual", kind: "Generacional", risk: "Supervivencia", base: "2012, con factor de mejora λₓ", orders: "2º y 1er orden", annex: "Anexo 1.1 (y 2.1 para el 1er orden)",
    uses: ["Seguros individuales en los que el riesgo es sobrevivir: rentas vitalicias y productos de jubilación.", "Cálculos en los que importa la generación del asegurado."],
    cons: ["Exige el año de nacimiento: la misma edad da resultados distintos según la generación.", "El factor de mejora proyecta una tendencia pasada; es una hipótesis, no un dato.", "Entre 11 y 85 años reproduce la Colectiva con un año de desfase (Ind[x] = Col[x−1])."] },
  { name: "PER2020 Colectiva", kind: "Generacional", risk: "Supervivencia", base: "2012, con factor de mejora λₓ", orders: "2º y 1er orden", annex: "Anexo 1.1 (y 2.1 para el 1er orden)",
    uses: ["Seguros colectivos de supervivencia, como los que instrumentan compromisos por pensiones.", "Comparar con la Individual el efecto de la selección del asegurado individual."],
    cons: ["Mismas exigencias que la Individual: generación y factor de mejora.", "Refleja un colectivo medio; no la selección de quien contrata por su cuenta."] },
  { name: "PASEM2020 General", kind: "Estática", risk: "Fallecimiento (vida-riesgo)", base: "2019 (año central)", orders: "2º orden; en 1er orden, Rel (×1,101875) y NoRel (×1,155)", annex: "Anexo 1.2",
    uses: ["Seguros de fallecimiento: vida-riesgo, temporales y coberturas vinculadas.", "Base de referencia para ajustar modelos paramétricos (así se han obtenido los valores iniciales de la calculadora)."],
    cons: ["No recoge la mejora futura de la mortalidad: correcto por prudencia en fallecimiento, pero inadecuada para rentas.", "El cierre por encima de 100 años no sigue una ley de mortalidad suave.", "No tiene sentido comparar generaciones con ella."] },
  { name: "PASEM2020 Decesos", kind: "Estática", risk: "Decesos", base: "2019 (año central)", orders: "2º orden y 1er orden (×1,101875)", annex: "Anexo 1.3",
    uses: ["Seguros de decesos.", "Comparar el nivel de mortalidad de este ramo con el de vida-riesgo."],
    cons: ["Sus qₓ son sensiblemente más altas que las de la General (del orden de 1,6 veces en muchas edades): no son intercambiables.", "Estática: no incorpora mejora de la mortalidad.", "Pensada para un ramo concreto; fuera de él no es representativa."] },
];

function NonParamAtlas() {
  return (
    <>
      <p className="lead">Cómo pasar de una tabla publicada a probabilidades para cualquier edad y plazo, y qué tabla usar en cada caso.</p>

      <section className="card prose">
        <h3>De la tabla a <S base="l" post="x" /></h3>
        <p>Las tablas publican <S base="q" post="x" /> en tanto por mil para edades enteras. Con ellas se construye una sola vez
          <Mth> <S base="l" post="0" /> = 100.000, &nbsp;<S base="l" post="x+1" /> = <S base="l" post="x" />(1 − <S base="q" post="x" />)</Mth>,
          con ω = 121, y todas las probabilidades salen como cocientes: <Mth><S pre="n" base="p" post="x" /> = <S base="l" post="x+n" /> / <S base="l" post="x" /></Mth>.</p>
        <p>En las generacionales, la <I>q</I> de cada edad se corrige según el año en que la cohorte la alcanza:
          <Mth> <S base="q" post="y" /> = <S base="q" post="y,2012" /> · e<sup>−λ<sub>y</sub>(C+y−2012)</sup></Mth>, con C el año de nacimiento.
          El <b>2º orden</b> es la mejor estimación; el <b>1er orden</b> añade los recargos técnicos de la resolución.</p>
      </section>

      <h3 className="famtitle">Interpolación entre edades enteras</h3>
      <div className="atlas-grid">
        {INTERP_ATLAS.map((a) => (
          <article key={a.name} className="acard">
            <header className="ahead"><div><h4>{a.name}</h4><p className="aorigin">{a.inApp ? "Disponible en la calculadora" : "Solo como referencia"}</p></div></header>
            <p className="aidea">{a.hyp}</p>
            <p className="aformula">{a.f}</p>
            <div className="acols">
              <div><h5>Ventajas</h5><ul>{a.pros.map((u, i) => <li key={i}>{u}</li>)}</ul></div>
              <div><h5>Desventajas</h5><ul>{a.cons.map((u, i) => <li key={i}>{u}</li>)}</ul></div>
            </div>
            <p className="arel"><b>Casos de uso.</b> {a.uses}</p>
          </article>
        ))}
      </div>

      <h3 className="famtitle">Tablas de mortalidad (BOE-A-2020-17154)</h3>
      <section className="card">
        <div className="tablewrap flat">
          <table className="sum">
            <thead><tr><th className="l">Tabla</th><th className="l">Tipo</th><th className="l">Riesgo cubierto</th><th className="l">Año base</th><th className="l">Órdenes</th></tr></thead>
            <tbody>{TABLE_ATLAS.map((t) => (
              <tr key={t.name}><td className="l"><b>{t.name}</b><span className="sub">{t.annex}</span></td><td className="l">{t.kind}</td><td className="l">{t.risk}</td><td className="l">{t.base}</td><td className="l">{t.orders}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </section>
      <div className="atlas-grid">
        {TABLE_ATLAS.map((t) => (
          <article key={t.name} className="acard">
            <header className="ahead"><div><h4>{t.name}</h4><p className="aorigin">{t.kind}. {t.risk}.</p></div></header>
            <div className="acols">
              <div><h5>Casos de uso</h5><ul>{t.uses.map((u, i) => <li key={i}>{u}</li>)}</ul></div>
              <div><h5>Desventajas y cautelas</h5><ul>{t.cons.map((u, i) => <li key={i}>{u}</li>)}</ul></div>
            </div>
          </article>
        ))}
      </div>
      <p className="caption">Por qué generacionales para supervivencia y estáticas para fallecimiento: ignorar la mejora de la mortalidad sobreestima las muertes futuras, lo que es prudente cuando se paga por fallecimiento y peligroso cuando se paga por sobrevivir.</p>
    </>
  );
}

export default function Atlas() {
  const [sub, setSub] = useState("param");
  return (
    <div className="atlas">
      <div className="seg-ctl atlas-switch" role="group" aria-label="Sección del atlas">
        {[["param", "Modelos paramétricos"], ["noparam", "Tablas e interpolación"]].map(([v, t]) => (
          <button key={v} type="button" aria-pressed={sub === v} className={sub === v ? "on" : ""} onClick={() => setSub(v)}>{t}</button>
        ))}
      </div>
      {sub === "param" ? <ParamAtlas /> : <NonParamAtlas />}
    </div>
  );
}

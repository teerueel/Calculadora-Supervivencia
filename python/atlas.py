"""Contenido del Atlas (HTML para QTextBrowser). Mismo texto que el artifact."""
from modelos import MODELS, MODEL_KEYS, MODEL_FAMILIES

SERIF = "'STIX Two Text', 'Cambria Math', Cambria, Georgia, serif"


def _m(s):
    return f"<span style=\"font-family:{SERIF}; font-size:15px\">{s}</span>"


MU = "<i>μ</i><sub>x</sub>"
PARAM_ATLAS = {
    "exponencial": dict(origin="Fuerza de mortalidad constante", shape="Constante", range="Tramos cortos de edad",
        idea="El riesgo de fallecer es el mismo a cualquier edad: no hay envejecimiento.",
        mu=f"{MU} = λ",
        uses=["Hipótesis de fuerza constante entre edades enteras para fraccionar la edad.", "Referencia frente a la que contrastar modelos con envejecimiento.", "Fiabilidad y riesgos sin desgaste en periodos cortos."],
        cons=["Falta de memoria: la probabilidad de sobrevivir t años no depende de la edad.", "Irreal para la vida humana en horizontes largos.", "La esperanza de vida completa es 1/λ a cualquier edad."],
        related="Es Weibull con β = 1 y Gompertz con c = 1."),
    "demoivre": dict(origin="Abraham de Moivre, 1725", shape="Creciente, diverge en ω", range="Docencia y fraccionamiento",
        idea="Los supervivientes decrecen linealmente hasta una edad límite ω: los fallecimientos se reparten por igual.",
        mu=f"{MU} = 1 / (ω − <i>x</i>)",
        uses=["Docencia y cálculo a mano: todo tiene forma cerrada sencilla.", "Fundamento de la hipótesis de distribución uniforme de fallecimientos (UDD) dentro del año.", "Aproximaciones rápidas en tramos cortos."],
        cons=["Fallecimientos constantes a todas las edades: infancia y edad adulta irreales.", "La fuerza de mortalidad solo crece de forma apreciable muy cerca de ω.", "Obliga a fijar ω desde fuera: ajustado a una tabla real, ω se dispara por encima de 160."],
        related="Ley de supervivencia uniforme: la base de la hipótesis UDD."),
    "gompertz": dict(origin="Benjamin Gompertz, 1825", shape="Exponencial creciente", range="Adultos, 30–90 años",
        idea="El riesgo de muerte se multiplica por c cada año de edad: log μ crece en línea recta.",
        mu=f"{MU} = <i>B c</i><sup><i>x</i></sup>",
        uses=["Mortalidad adulta humana, en seguros de vida y de rentas.", "Graduación de tablas y extrapolación en edades adultas.", "Punto de partida de Makeham, Perks, Kannisto y Heligman–Pollard."],
        cons=["Ignora la mortalidad infantil y la joroba de accidentes juvenil.", "Sobreestima la mortalidad a edades muy avanzadas: no se desacelera.", "No incluye mortalidad independiente de la edad."],
        related="Makeham con A = 0."),
    "makeham": dict(origin="William Makeham, 1860", shape="Constante más exponencial", range="Adultos, 20–90 años",
        idea="Añade a Gompertz un término A de mortalidad accidental, igual a cualquier edad.",
        mu=f"{MU} = <i>A</i> + <i>B c</i><sup><i>x</i></sup>",
        uses=["Graduación clásica de tablas de asegurados.", "Seguros sobre varias vidas: permite sustituir el grupo por una única vida de edad equivalente.", "Primas y reservas con expresiones analíticas."],
        cons=["El término constante no reproduce la joroba de accidentes de los 18–25 años.", "Hereda la sobreestimación de Gompertz en la vejez extrema.", "A y B están muy correlacionados al estimar."],
        related="Gompertz si A = 0; Siler le añade un término infantil."),
    "weibull": dict(origin="Waloddi Weibull, 1951", shape="Potencial: decrece, constante o crece", range="Fiabilidad y estudios clínicos",
        idea="La fuerza de mortalidad es una potencia de la edad; la forma β decide si decrece, se mantiene o crece.",
        mu=f"{MU} = (β/θ)(<i>x</i>/θ)<sup>β−1</sup>",
        uses=["Fiabilidad e ingeniería: tiempo hasta el fallo.", "Supervivencia clínica: tiempo desde el diagnóstico o el tratamiento.", "Modelos paramétricos de riesgos proporcionales."],
        cons=["Crece de forma polinómica: ajusta peor que Gompertz la mortalidad adulta humana.", "En x = 0 la fuerza de mortalidad es infinita si β < 1 y nula si β > 1.", "Siempre monótona: no genera forma de bañera."],
        related="Exponencial si β = 1."),
    "perks": dict(origin="Wilfred Perks, 1932", shape="Sigmoide, se estabiliza en B/D", range="Adultos y edades avanzadas",
        idea="Versión logística de Makeham: el crecimiento exponencial se frena y μ tiende a la meseta B/D.",
        mu=f"{MU} = (<i>A</i> + <i>B c</i><sup><i>x</i></sup>) / (1 + <i>D c</i><sup><i>x</i></sup>)",
        uses=["Mortalidad en edades avanzadas con desaceleración (meseta).", "Tablas de rentas vitalicias, donde no conviene sobreestimar la mortalidad en la vejez.", "Se justifica por heterogeneidad: fragilidad gamma sobre Makeham (modelo de Beard)."],
        cons=["Cuatro parámetros difíciles de identificar con pocos datos en edades altas.", "La meseta la determinan muy pocas observaciones extremas.", "Sin componente infantil ni de accidentes."],
        related="Makeham si D = 0; Kannisto si A = 0 y B = D."),
    "kannisto": dict(origin="Väinö Kannisto, 1992", shape="Logístico, tiende a 1", range="Edades de 80 en adelante",
        idea="Logística de dos parámetros pensada para cerrar la tabla en edades muy avanzadas, con μ acotada por 1.",
        mu=f"{MU} = <i>a e</i><sup><i>bx</i></sup> / (1 + <i>a e</i><sup><i>bx</i></sup>)",
        uses=["Suavizado y extrapolación de la mortalidad a partir de los 80 años.", "Método con el que la Human Mortality Database cierra sus tablas en edades altas.", "Estudios de longevidad extrema."],
        cons=["Solo válido en la vejez: no sirve para una tabla completa.", "Asíntota fija en 1, sin parámetro propio para la meseta.", "Muy sensible a la calidad de los datos en edades extremas."],
        related="Perks con A = 0 y B = D."),
    "thiele": dict(origin="Thorvald Thiele, 1871", shape="Bañera con joroba", range="Todas las edades",
        idea="Primera ley para toda la vida: término infantil decreciente, joroba juvenil gaussiana y senescencia de Gompertz.",
        mu=f"{MU} = <i>a</i><sub>1</sub>e<sup>−<i>b</i><sub>1</sub><i>x</i></sup> + <i>a</i><sub>2</sub>e<sup>−½<i>b</i><sub>2</sub>(<i>x</i>−<i>c</i>)²</sup> + <i>a</i><sub>3</sub>e<sup><i>b</i><sub>3</sub><i>x</i></sup>",
        uses=["Representar la tabla completa de 0 a 120 años con una única expresión.", "Descomponer la mortalidad por etapas vitales.", "Antecedente directo de Heligman–Pollard."],
        cons=["Siete parámetros: estimación inestable y muy correlacionada.", "La joroba gaussiana es simétrica; la real sube más deprisa de lo que baja.", "Con la PASEM2020 de mujeres la joroba casi desaparece y el modelo degenera en Siler."],
        related="Siler si la joroba se sustituye por una constante."),
    "siler": dict(origin="William Siler, 1979", shape="Bañera", range="Todas las edades",
        idea="Tres riesgos en competencia: inmadurez (decreciente), fondo constante y senescencia (Gompertz).",
        mu=f"{MU} = <i>a</i><sub>1</sub>e<sup>−<i>b</i><sub>1</sub><i>x</i></sup> + <i>a</i><sub>2</sub> + <i>a</i><sub>3</sub>e<sup><i>b</i><sub>3</sub><i>x</i></sup>",
        uses=["Curvas en bañera en demografía, ecología y paleodemografía.", "Comparar poblaciones humanas y animales con pocos parámetros.", "Ajustes con datos escasos o edades agrupadas."],
        cons=["No recoge la joroba de accidentes juvenil.", "Parámetros muy correlacionados, sobre todo a₂ con a₃.", "Hereda la sobreestimación de Gompertz en la vejez extrema."],
        related="Makeham más un término infantil."),
    "heligman_pollard": dict(origin="Larry Heligman y John Pollard, 1980", shape="Bañera con joroba", range="Todas las edades",
        idea="Modela el cociente q/p con tres sumandos con significado demográfico: infancia, joroba de accidentes y senescencia.",
        mu="<i>q</i><sub>x</sub>/<i>p</i><sub>x</sub> = <i>A</i><sup>(<i>x</i>+<i>B</i>)<sup><i>C</i></sup></sup> + <i>D</i>e<sup>−<i>E</i>(ln <i>x</i> − ln <i>F</i>)²</sup> + <i>G H</i><sup><i>x</i></sup>",
        uses=["Graduación de tablas completas en demografía y en el sector asegurador.", "Proyección de la mortalidad modelando la evolución de sus parámetros.", "Interpretación directa: cada parámetro tiene lectura demográfica."],
        cons=["Ocho parámetros: mínimos locales y dependencia de los valores iniciales.", "Es discreto, sobre qₓ: la fuerza de mortalidad depende de cómo se fraccione la edad.", "La componente senescente sobreestima en edades muy altas."],
        related="Descendiente de Thiele, con la joroba lognormal en lugar de gaussiana."),
}

INTERP_ATLAS = [
    dict(name="Lineal (UDD)", inapp=True,
         hyp="Los fallecimientos del año se reparten uniformemente: l<sub>x+s</sub> es una recta entre l<sub>x</sub> y l<sub>x+1</sub>.",
         f="<sub>s</sub><i>p</i><sub>x</sub> = 1 − <i>s</i>·<i>q</i><sub>x</sub> &nbsp;&nbsp; <i>μ</i><sub>x+s</sub> = <i>q</i><sub>x</sub> / (1 − <i>s</i>·<i>q</i><sub>x</sub>)",
         pros=["La más sencilla de aplicar a mano.", "e̊ₓ = eₓ + ½ de forma exacta.", "Base de las aproximaciones habituales para pagos fraccionados."],
         cons=["μ crece dentro del año y salta en cada edad entera.", "Con qₓ = 1, μ se dispara al final del último año."],
         uses="Primas y rentas fraccionadas, edades actuariales no enteras, cálculo a mano."),
    dict(name="Exponencial (fuerza constante)", inapp=True,
         hyp="La fuerza de mortalidad es constante dentro de cada año: l<sub>x+s</sub> decrece exponencialmente.",
         f="<sub>s</sub><i>p</i><sub>x</sub> = <i>p</i><sub>x</sub><sup><i>s</i></sup> &nbsp;&nbsp; <i>μ</i><sub>x+s</sub> = −ln <i>p</i><sub>x</sub>",
         pros=["Coherente con modelos en tiempo continuo y con la exposición al riesgo.", "Multiplicativa: la supervivencia de varios tramos se encadena sin error.", "Es la hipótesis natural cuando se trabaja con tantos centrales de mortalidad."],
         cons=["μ es escalonada: constante dentro del año y con saltos en las edades enteras.", "Con qₓ = 1 la supervivencia cae a cero en cuanto empieza el año."],
         uses="Estimación de tasas a partir de exposición, modelos multiestado, fraccionamiento en valoración continua."),
    dict(name="Balducci (hiperbólica)", inapp=False,
         hyp="La probabilidad de fallecer en el resto del año es proporcional al tiempo que queda: <sub>1−s</sub>q<sub>x+s</sub> = (1 − s)·q<sub>x</sub>.",
         f="<sub>s</sub><i>p</i><sub>x</sub> = <i>p</i><sub>x</sub> / (1 − (1 − <i>s</i>)·<i>q</i><sub>x</sub>) &nbsp;&nbsp; <i>μ</i><sub>x+s</sub> = <i>q</i><sub>x</sub> / (1 − (1 − <i>s</i>)·<i>q</i><sub>x</sub>)",
         pros=["Históricamente cómoda para estimar qₓ a partir de expuestos al riesgo.", "Da expresiones sencillas para las probabilidades del resto del año."],
         cons=["μ decrece dentro del año: contrario a la mortalidad adulta real.", "Hoy casi no se usa fuera del contexto histórico."],
         uses="Referencia histórica; no está implementada en la calculadora."),
]

TABLE_ATLAS = [
    dict(name="PER2020 Individual", kind="Generacional", risk="Supervivencia", base="2012, con factor de mejora λₓ", orders="2º y 1er orden", annex="Anexo 1.1 (y 2.1 para el 1er orden)",
         uses=["Seguros individuales en los que el riesgo es sobrevivir: rentas vitalicias y productos de jubilación.", "Cálculos en los que importa la generación del asegurado."],
         cons=["Exige el año de nacimiento: la misma edad da resultados distintos según la generación.", "El factor de mejora proyecta una tendencia pasada; es una hipótesis, no un dato.", "Entre 11 y 85 años reproduce la Colectiva con un año de desfase (Ind[x] = Col[x−1])."]),
    dict(name="PER2020 Colectiva", kind="Generacional", risk="Supervivencia", base="2012, con factor de mejora λₓ", orders="2º y 1er orden", annex="Anexo 1.1 (y 2.1 para el 1er orden)",
         uses=["Seguros colectivos de supervivencia, como los que instrumentan compromisos por pensiones.", "Comparar con la Individual el efecto de la selección del asegurado individual."],
         cons=["Mismas exigencias que la Individual: generación y factor de mejora.", "Refleja un colectivo medio; no la selección de quien contrata por su cuenta."]),
    dict(name="PASEM2020 General", kind="Estática", risk="Fallecimiento (vida-riesgo)", base="2019 (año central)", orders="2º orden; en 1er orden, Rel (×1,101875) y NoRel (×1,155)", annex="Anexo 1.2",
         uses=["Seguros de fallecimiento: vida-riesgo, temporales y coberturas vinculadas.", "Base de referencia para ajustar modelos paramétricos (así se han obtenido los valores iniciales de la calculadora)."],
         cons=["No recoge la mejora futura de la mortalidad: correcto por prudencia en fallecimiento, pero inadecuada para rentas.", "El cierre por encima de 100 años no sigue una ley de mortalidad suave.", "No tiene sentido comparar generaciones con ella."]),
    dict(name="PASEM2020 Decesos", kind="Estática", risk="Decesos", base="2019 (año central)", orders="2º orden y 1er orden (×1,101875)", annex="Anexo 1.3",
         uses=["Seguros de decesos.", "Comparar el nivel de mortalidad de este ramo con el de vida-riesgo."],
         cons=["Sus qₓ son sensiblemente más altas que las de la General (del orden de 1,6 veces en muchas edades): no son intercambiables.", "Estática: no incorpora mejora de la mortalidad.", "Pensada para un ramo concreto; fuera de él no es representativa."]),
]

CSS = """
body { font-family: 'Public Sans', 'Segoe UI', sans-serif; font-size: 13.5px; color: #1B2A38; }
h2 { font-family: %(s)s; font-size: 21px; font-weight: 600; margin: 16px 0 6px 0; }
h3 { font-family: %(s)s; font-size: 18px; font-weight: 600; margin: 4px 0 0 0; }
.muted { color: #5B6B7A; }
.small { font-size: 12px; }
td { vertical-align: top; }
th { background: #F6F8FA; color: #5B6B7A; font-size: 12px; text-align: left; }
.big { font-family: %(s)s; font-size: 26px; }
""" % {"s": SERIF}


def _ul(items):
    return "<ul style='margin:2px 0 0 -18px'>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def _card(inner):
    return ("<table width='100%' cellspacing='0' cellpadding='12' style='border:1px solid #D9E0E6; background:#FFFFFF; margin-bottom:10px'>"
            f"<tr><td>{inner}</td></tr></table>")


def param_html():
    rows = "".join(
        f"<tr><td><b>{MODELS[k]['name']}</b><br><span class='muted small'>{a['origin']}</span></td>"
        f"<td align='center'><span class='big'>{len(MODELS[k]['params'])}</span></td><td>{a['shape']}</td><td>{a['range']}</td><td>{a['cons'][0]}</td></tr>"
        for k, a in PARAM_ATLAS.items())
    out = [f"<html><head><style>{CSS}</style></head><body>",
           "<p style='font-size:14.5px'>Diez leyes de mortalidad, de la más simple a las que describen la vida completa. "
           "Cada miniatura dibuja log μ entre 0 y 110 años con los valores iniciales de la calculadora (hombre).</p>",
           "<table width='100%' cellspacing='0' cellpadding='8' border='0' style='border:1px solid #D9E0E6; background:#FFFFFF'>"
           "<tr><th>Modelo</th><th>Parámetros</th><th>Forma de μ</th><th>Tramo de edades</th><th>Principal limitación</th></tr>"
           + rows + "</table>"]
    for fam in MODEL_FAMILIES:
        out.append(f"<h2>{fam}</h2>")
        for k in [k for k in MODEL_KEYS if MODELS[k]["family"] == fam]:
            a, m = PARAM_ATLAS[k], MODELS[k]
            n = len(m["params"])
            pn = " &nbsp; ".join(f"<i style='font-family:{SERIF}; font-size:14px'>{p['sym']}</i> <span class='muted'>{p['desc']}</span>" for p in m["params"])
            inner = (
                "<table width='100%' cellspacing='0' cellpadding='0'><tr>"
                f"<td><h3>{m['name']}</h3><span class='muted small'>{a['origin']}</span></td>"
                f"<td align='right'><span class='big'>{n}</span><br><span class='muted small'>{'parámetro' if n == 1 else 'parámetros'}</span></td></tr></table>"
                f"<p><img src='spark_{k}' width='220' height='56'></p>"
                f"<p>{_m(a['mu'])}</p><p>{a['idea']}</p><p class='small'>{pn}</p>"
                "<table width='100%' cellspacing='0' cellpadding='4'><tr>"
                f"<td width='50%'><b class='muted small'>Casos de uso</b>{_ul(a['uses'])}</td>"
                f"<td width='50%'><b class='muted small'>Desventajas</b>{_ul(a['cons'])}</td></tr></table>"
                f"<p class='muted small'>{a['related']}</p>")
            out.append(_card(inner))
    out.append("</body></html>")
    return "".join(out)


def nonparam_html():
    out = [f"<html><head><style>{CSS}</style></head><body>",
           "<p style='font-size:14.5px'>Cómo pasar de una tabla publicada a probabilidades para cualquier edad y plazo, y qué tabla usar en cada caso.</p>",
           _card("<h3>De la tabla a <i>l</i><sub>x</sub></h3>"
                 "<p>Las tablas publican <i>q</i><sub>x</sub> en tanto por mil para edades enteras. Con ellas se construye una sola vez "
                 + _m("<i>l</i><sub>0</sub> = 100.000, &nbsp;<i>l</i><sub>x+1</sub> = <i>l</i><sub>x</sub>(1 − <i>q</i><sub>x</sub>)")
                 + ", con ω = 121, y todas las probabilidades salen como cocientes: "
                 + _m("<sub>n</sub><i>p</i><sub>x</sub> = <i>l</i><sub>x+n</sub> / <i>l</i><sub>x</sub>") + ".</p>"
                 "<p>En las generacionales, la <i>q</i> de cada edad se corrige según el año en que la cohorte la alcanza: "
                 + _m("<i>q</i><sub>y</sub> = <i>q</i><sub>y,2012</sub> · e<sup>−λ<sub>y</sub>(C+y−2012)</sup>")
                 + ", con C el año de nacimiento. El <b>2º orden</b> es la mejor estimación; el <b>1er orden</b> añade los recargos técnicos de la resolución.</p>"),
           "<h2>Interpolación entre edades enteras</h2>"]
    for a in INTERP_ATLAS:
        out.append(_card(
            f"<h3>{a['name']}</h3><span class='muted small'>{'Disponible en la calculadora' if a['inapp'] else 'Solo como referencia'}</span>"
            f"<p>{a['hyp']}</p><p>{_m(a['f'])}</p>"
            "<table width='100%' cellspacing='0' cellpadding='4'><tr>"
            f"<td width='50%'><b class='muted small'>Ventajas</b>{_ul(a['pros'])}</td>"
            f"<td width='50%'><b class='muted small'>Desventajas</b>{_ul(a['cons'])}</td></tr></table>"
            f"<p class='muted small'><b>Casos de uso.</b> {a['uses']}</p>"))
    out.append("<h2>Tablas de mortalidad (BOE-A-2020-17154)</h2>")
    rows = "".join(f"<tr><td><b>{t['name']}</b><br><span class='muted small'>{t['annex']}</span></td><td>{t['kind']}</td><td>{t['risk']}</td><td>{t['base']}</td><td>{t['orders']}</td></tr>"
                   for t in TABLE_ATLAS)
    out.append("<table width='100%' cellspacing='0' cellpadding='8' style='border:1px solid #D9E0E6; background:#FFFFFF; margin-bottom:10px'>"
               "<tr><th>Tabla</th><th>Tipo</th><th>Riesgo cubierto</th><th>Año base</th><th>Órdenes</th></tr>" + rows + "</table>")
    for t in TABLE_ATLAS:
        out.append(_card(
            f"<h3>{t['name']}</h3><span class='muted small'>{t['kind']}. {t['risk']}.</span>"
            "<table width='100%' cellspacing='0' cellpadding='4'><tr>"
            f"<td width='50%'><b class='muted small'>Casos de uso</b>{_ul(t['uses'])}</td>"
            f"<td width='50%'><b class='muted small'>Desventajas y cautelas</b>{_ul(t['cons'])}</td></tr></table>"))
    out.append("<p class='muted small'>Por qué generacionales para supervivencia y estáticas para fallecimiento: ignorar la mejora de la mortalidad "
               "sobreestima las muertes futuras, lo que es prudente cuando se paga por fallecimiento y peligroso cuando se paga por sobrevivir.</p>")
    out.append("</body></html>")
    return "".join(out)

# Nota técnica de la Calculadora de supervivencia

Base técnica de todos los cálculos que realiza la calculadora: datos, hipótesis, fórmulas y
controles. Describe lo que está **implementado**, no lo planificado.

| | |
| --- | --- |
| Versión de la nota | 1.1 |
| Fecha | 7 de octubre de 2026 |
| Estado del producto | Tablas, modelos paramétricos, comparación, rentas actuariales y atlas |
| Implementaciones | Python (`python/`) y JavaScript (`web/src/`), numéricamente equivalentes |

> **Mantenimiento.** Esta nota se actualiza en el mismo commit que cualquier cambio que
> altere un cálculo, añada una magnitud o cambie una hipótesis. Cada actualización sube la
> versión y deja una línea en el §11.

* * *

## 1. Alcance y principios

La calculadora obtiene probabilidades de supervivencia y fallecimiento, esperanzas de vida y
la distribución completa del valor actual de rentas actuariales, sobre una cabeza, a partir
de tablas de mortalidad oficiales españolas o de leyes paramétricas.

Tres principios rigen todos los cálculos:

1. **Una única función de supervivencia.** Para cada escenario se construye una vez $l_x$ y
   todas las magnitudes se obtienen como cocientes o diferencias de sus valores. No se usan
   productorios $\prod(1-q_{x+k})$ ni sumatorios acumulados de probabilidades.
2. **No se inventan datos.** Solo se usan las $q_x$ publicadas. En edades no enteras se
   reparte dentro del año la mortalidad publicada, bajo una hipótesis declarada.
3. **Trazabilidad.** Cada dato procede de una fuente identificada (§2) y cada hipótesis es
   visible en la interfaz.

**Notación.** Actuarial internacional: $_n p_x$, $_n q_x$, $_{m\mid n} q_x$, $e_x$,
$\mathring e_x$, $\mu_x$; rentas $_{k\mid}\ddot a^{(m)}_{x:\overline{n}|}$ y
$_{k\mid}a^{(m)}_{x:\overline{n}|}$.

## 2. Fuentes de datos

**Tablas biométricas.** Resolución de la Dirección General de Seguros y Fondos de Pensiones
de 17 de diciembre de 2020, BOE núm. 338, de 28 de diciembre de 2020
([BOE-A-2020-17154](https://www.boe.es/buscar/doc.php?id=BOE-A-2020-17154)):

| Anexo | Contenido | Uso en la calculadora |
| --- | --- | --- |
| 1.1 | PER2020 Colectiva e Individual, 2º orden: $q_x$ base 2012 y $\lambda_x$ | Datos de partida |
| 1.2 | PASEM2020 General (vida-riesgo), 2º orden, base 2019 | Datos de partida |
| 1.3 | PASEM2020 Decesos, 2º orden, base 2019 | Datos de partida |
| 2.1 | PER2020 Individual, 1er orden: $q_x$ base 2012 y $\lambda_x$ | Datos de partida, tal cual |
| 2.1 | Recargos técnicos de la PER2020 Colectiva para el 1er orden | Derivación de la Colectiva de 1er orden (§3.3) |
| 2.2–2.4 | PASEM2020 de 1er orden: Rel, NoRel y Decesos | Derivación (§3.3) |

Edades 0 a 120, por sexo. Las $q_x$ se publican en tanto por mil.

**Verificación.** `python/verificacion_boe.py` compara casilla por casilla los datos del
código con los anexos extraídos del PDF (`python/boe_anexos.json`) y forma parte de los
tests automáticos (§9). Los anexos 1.1, 1.2, 1.3, los recargos del 2.1 y la PER2020
Individual de 1er orden coinciden exactamente. Las tablas de primer orden derivadas (PER2020
Colectiva y PASEM2020) difieren de las publicadas como máximo en 0,001 ‰ en $q_x$ (máximo
medido: 0,0009 ‰) y en una unidad del cuarto decimal en $\lambda_x$, por el redondeo con que
las publica el BOE (lo advierte su apartado séptimo). Esas son las tolerancias del cotejo;
las diferencias no se corrigen.

## 3. Construcción del vector de mortalidad

Para cada tabla, sexo y, si procede, cohorte, se obtiene $q_y$ para $y = 0,\dots,120$.
Todo valor se divide entre 1000, se acota a $[0,1]$ y se fuerza $q_{120} = 1$.

### 3.1 Tablas generacionales (PER2020)

Se sigue la diagonal de la generación. Con año de cálculo $A$ y edad $x$, la cohorte es
$C = A - \lfloor x \rfloor$ y

$$q_y = \frac{q^{\,2012}_y}{1000}\; e^{-\lambda_y\,(C + y - 2012)} .$$

El exponente usa el año en que la cohorte alcanza la edad $y$, $C+y$, no el año de cálculo.
El año de cálculo debe ser entero entre 1900 y 2200.

### 3.2 Tablas estáticas (PASEM2020)

$q_y = q^{\,2019}_y / 1000$, sin factor de mejora.

### 3.3 Derivaciones

**PER2020 Individual a partir de la Colectiva** (anexo 1.1):
$\text{Ind}[x] = \text{Col}[x-1]$ para $x \in [11, 85]$; idénticas en 0–10 y 97–120;
valores propios tabulados en 86–96. Aplica a $q_x$ y a $\lambda_x$.

**PER2020 Colectiva de primer orden** (anexo 2.1), con el recargo de $q$ expresado en tanto
por ciento:

$$q^{(1)}_{\text{base}} = q^{(2)}_{\text{base}}\left(1 - \tfrac{r_q}{100}\right),\qquad
\lambda^{(1)} = \lambda^{(2)} + r_\lambda .$$

**PER2020 Individual de primer orden:** se toma **tal cual** de la tabla publicada en el
anexo 2.1 ($q_x$ base 2012 y $\lambda_x$), sin derivarla. Los recargos del anexo están
tabulados solo para la Colectiva; los de la Individual en 86–96 no se publican y
reconstruirlos (versión 1.0) desviaba $q_x$ hasta 0,007 ‰ y $\lambda_x$ hasta $10^{-4}$, con
efecto de hasta $8{,}6\cdot10^{-4}$ en $_n p_x$ (hombre, $x = 47$, $n = 50$, año 2026).
Aplicar sin más los recargos de la Colectiva desviaría $_n p_x$ hasta $6\cdot10^{-4}$.

**PASEM2020 de primer orden** (anexos 2.2–2.4), acotando a 1000 ‰:

| Tabla | Factor sobre la de 2º orden |
| --- | --- |
| Rel (vida-riesgo vinculado) | $\times\,1{,}101875$ sobre la General |
| NoRel (resto de vida-riesgo) | $\times\,1{,}155$ sobre la General |
| Decesos | $\times\,1{,}101875$ sobre Decesos |

### 3.4 Catálogo resultante

Nueve tablas: PER2020 Individual y Colectiva (2º y 1er orden), PASEM2020 General (2º orden),
Rel y NoRel (1er orden), Decesos (2º y 1er orden).

## 4. Función de supervivencia

$$l_0 = 100\,000,\qquad l_{y+1} = l_y\,(1 - q_y),\quad y = 0,\dots,120 .$$

Resulta un vector de 122 posiciones con $\omega = 121$ y $l_{121} = 0$. Cualquier lectura
fuera de $[0, \omega)$ vale 0.

## 5. Edades no enteras

$l$ solo se construye en edades enteras. Para $a = y + s$, con $y$ entero y $0 < s < 1$, se
reparte la mortalidad publicada del año $y$ según la hipótesis elegida por el usuario:

| Hipótesis | $l_{y+s}$ | $_s p_y$ | $\mu_{y+s}$ |
| --- | --- | --- | --- |
| Lineal (UDD) | $l_y - s\,(l_y - l_{y+1})$ | $1 - s\,q_y$ | $\dfrac{q_y}{1 - s\,q_y}$ |
| Exponencial ($\mu$ constante) | $l_y\,p_y^{\,s}$ | $p_y^{\,s}$ | $-\ln p_y$ |

En $[120, 121)$, $q_{120} = 1$ y $\mu$ no está definida; no se representa. La hipótesis de
Balducci se describe en el Atlas como referencia, pero no se usa en los cálculos.

## 6. Probabilidades y esperanzas de vida

Con $x$, $n$ y $m$ reales no negativos y $l$ interpolada según el §5:

| Magnitud | Fórmula | Significado |
| --- | --- | --- |
| $_n p_x$ | $l_{x+n}/l_x$ | $(x)$ sobrevive $n$ años |
| $_n q_x$ | $1 - {}_n p_x$ | $(x)$ fallece antes de $x+n$ |
| $_{m\mid n} q_x$ | $(l_{x+m} - l_{x+m+n})/l_x$ | $(x)$ fallece entre $x+m$ y $x+m+n$ |
| $_m q_x$ | $1 - l_{x+m}/l_x$ | fallece antes del diferimiento |
| $_{m+n} p_x$ | $l_{x+m+n}/l_x$ | sobrevive a todo el horizonte |

**Esperanza de vida abreviada:** $e_x = \sum_{k \ge 1} l_{x+k}/l_x$, sumando mientras
$x + k < \omega$.

**Esperanza de vida completa**, exacta bajo la hipótesis elegida, integrando $l$ tramo a
tramo:

$$\mathring e_x = \frac{1}{l_x}\int_x^{\omega} l_a\,da,\qquad
\int_{s_0}^{1} l_{y+s}\,ds =
\begin{cases}
l_y(1-s_0) - \tfrac12\,d_y\,(1-s_0^2) & \text{lineal}\\[4pt]
l_y\,\dfrac{p_y - p_y^{\,s_0}}{\ln p_y} & \text{exponencial}
\end{cases}$$

con $d_y = l_y - l_{y+1}$. No se usa la aproximación $e_x + \tfrac12$.

**Validación y casos límite.** $x \in [0, 120]$; $n, m \ge 0$. Si $x + m + n > \omega$ se
avisa. Si $l_x = 0$, las probabilidades condicionadas a $(x)$ no están definidas y se
muestra un error en lugar de un número.

**Identidad de control:** $_m q_x + {}_{m\mid n} q_x + {}_{m+n} p_x = 1$. Es la única
partición exacta de la unidad entre estas magnitudes; $_{m\mid n} q_x$ se solapa con
$_n p_x$ y $_n q_x$.

**Curvas.** Se representan, como funciones de la vida residual $T(x)$, la supervivencia
$_t p_x$, la función de distribución $_t q_x = 1 - {}_t p_x$ y el tanto instantáneo
$\mu_{x+t}$ (escala logarítmica o lineal), en una rejilla de paso $t = 0{,}25$ desde 0
hasta $\omega - x$.

## 7. Modelos paramétricos

### 7.1 Modelos continuos

Cada modelo se define por su tanto instantáneo $\mu(x)$ y su integral
$H(x) = \int_0^x \mu(s)\,ds$. Entonces $S(x) = e^{-H(x)}$ hace de $l_x/l_0$ y se toma

$$l_x = 100\,000\cdot S(x),$$

con las mismas fórmulas del §6, válidas en cualquier edad real sin interpolar. Si $H$
diverge o no es finita, $S = 0$.

| Modelo | $\mu_x$ | $H(x)$ | Parámetros |
| --- | --- | --- | --- |
| Exponencial | $\lambda$ | $\lambda x$ | 1 |
| De Moivre | $\dfrac{1}{\omega - x}$ | $-\ln\!\left(1 - \tfrac{x}{\omega}\right)$, $x<\omega$ | 1 |
| Gompertz | $B c^x$ | $\dfrac{B}{\ln c}(c^x - 1)$ | 2 |
| Makeham | $A + B c^x$ | $Ax + \dfrac{B}{\ln c}(c^x - 1)$ | 3 |
| Weibull | $\dfrac{\beta}{\theta}\left(\dfrac{x}{\theta}\right)^{\beta-1}$ | $\left(\dfrac{x}{\theta}\right)^{\beta}$ | 2 |
| Perks | $\dfrac{A + B c^x}{1 + D c^x}$ | $Ax + \dfrac{B - AD}{D\ln c}\left[\ln(1 + Dc^x) - \ln(1 + D)\right]$ | 4 |
| Kannisto | $\dfrac{a e^{bx}}{1 + a e^{bx}}$ | $\dfrac{1}{b}\left[\ln(1 + a e^{bx}) - \ln(1 + a)\right]$ | 2 |
| Thiele | $a_1 e^{-b_1 x} + a_2 e^{-\frac12 b_2 (x-c)^2} + a_3 e^{b_3 x}$ | cerrada, con $\Phi$ normal (abajo) | 7 |
| Siler | $a_1 e^{-b_1 x} + a_2 + a_3 e^{b_3 x}$ | $\dfrac{a_1}{b_1}(1 - e^{-b_1 x}) + a_2 x + \dfrac{a_3}{b_3}(e^{b_3 x} - 1)$ | 5 |

Para Thiele:

$$H(x) = \frac{a_1}{b_1}(1 - e^{-b_1 x})
+ a_2\sqrt{\frac{2\pi}{b_2}}\left[\Phi\!\big(\sqrt{b_2}(x - c)\big) - \Phi\!\big(-\sqrt{b_2}\,c\big)\right]
+ \frac{a_3}{b_3}(e^{b_3 x} - 1).$$

**Esperanza de vida completa.** Forma cerrada en el exponencial ($1/\lambda$) y en De Moivre
($(\omega - x)/2$). En el resto, $\mathring e_x = \int_0^\infty {}_t p_x\,dt$ por la regla de
Simpson con paso $h = 0{,}05$, hasta que $_t p_x < 10^{-12}$ o $t = 500$.

### 7.2 Heligman–Pollard (discreto)

$$\frac{q_x}{p_x} = A^{(x+B)^C} + D\,e^{-E(\ln x - \ln F)^2} + G H^x,\qquad
q_x = \frac{r_x}{1 + r_x},$$

donde $r_x$ es el miembro derecho; en $x = 0$ se omite el término central. Se evalúa en
edades enteras $0,\dots,120$, se acota a $[0,1]$, se fuerza $q_{120} = 1$ y se trata
exactamente como una tabla (§§4–6), incluida la interpolación en edades no enteras.

### 7.3 Valores iniciales de los parámetros

**No son valores publicados.** Proceden de un ajuste propio por mínimos cuadrados a la
PASEM2020 General de 2º orden de cada sexo, reproducible con `python/ajuste_presets.py`:
sobre $S(x)$ en el exponencial; sobre $\ln q_x$ en 30–100 (Gompertz, Makeham, Weibull,
Perks), 80–100 (Kannisto) y 0–100 (Thiele, Siler, Heligman–Pollard). De Moivre se fija en
$\omega = 121$ porque su ajuste diverge. La interfaz lo indica.

## 8. Rentas actuariales

### 8.1 Planteamiento

Renta sobre una cabeza de edad $x$ entera, con $m$ pagos al año, diferimiento $k$, duración
$n$ (temporal) o vitalicia, prepagable o postpagable. Cuantía por plazo $c$ y cuantía
anual $C = m\,c$. Tipo efectivo anual constante $I$, $v = (1+I)^{-1}$; cada plazo $1/m$ se
descuenta con $v^{1/m}$. Edad máxima $w = 120$; en la vitalicia $n = w + 1 - x - k$.

Se exige $n$ y $k$ múltiplos de $1/m$, $c > 0$, $I > -1$, $l_x > 0$ con la tabla elegida
(si nadie llega a la edad $x$ se muestra un error, no un resultado) y, en la vitalicia,
$x + k < 121$.

Rentas financieras unitarias:

$$a^{(m)}_{\overline{t}|} = \sum_{i=1}^{mt} \frac{v^{i/m}}{m},\qquad
\ddot a^{(m)}_{\overline{t}|} = \sum_{i=1}^{mt} \frac{v^{(i-1)/m}}{m},\qquad
{}_{k\mid}a^{(m)}_{\overline{t}|} = v^k\,a^{(m)}_{\overline{t}|}.$$

### 8.2 Distribución del valor actual

El valor actual de la renta es una variable aleatoria discreta $Y$, que se denota con el
propio símbolo de la renta. Con $N = m\,n$ plazos y probabilidades leídas de $l$,
$_{t\mid h}q_x = (l_{x+t} - l_{x+t+h})/l_x$:

| Prepagable ${}_{k\mid}\ddot a^{(m)}_{x:\overline{n}|}$ | Postpagable ${}_{k\mid}a^{(m)}_{x:\overline{n}|}$ |
| --- | --- |
| $0$ con prob. $_k q_x$ (solo si $k > 0$) | $0$ con prob. $_{k+1/m} q_x$ |
| $C\cdot{}_{k\mid}\ddot a^{(m)}_{\overline{j/m}|}$ con prob. $_{k+\frac{j-1}{m}\mid\frac1m} q_x$, $j = 1,\dots,N$ | $C\cdot{}_{k\mid}a^{(m)}_{\overline{j/m}|}$ con prob. $_{k+\frac{j}{m}\mid\frac1m} q_x$, $j = 1,\dots,N-1$ |
| al último valor se le suma $_{k+n} p_x$ (temporal) | $C\cdot{}_{k\mid}a^{(m)}_{\overline{n}|}$ con prob. $_{k+n} p_x$ (temporal) |

En la vitalicia no hay término de supervivencia, porque $_{w+1-x}p_x = 0$. Las edades
$x + j/m$ no enteras usan siempre interpolación lineal (UDD), con independencia de la
hipótesis elegida en la pestaña de tablas. Las rentas se calculan sobre las tablas del
catálogo; los modelos paramétricos no intervienen.

### 8.3 Momentos y métricas

- Momentos ordinarios de los órdenes elegidos: $E[Y^s] = \sum_i y_i^{\,s}\,p_i$ (en €$^s$).
- Media $E[Y]$, que es la prima pura única.
- Varianza $\sigma^2 = E[Y^2] - E[Y]^2$, desviación típica $\sigma$ y coeficiente de
  variación $\sigma/E[Y]$.
- Asimetría $\mu_3/\sigma^3$ y curtosis $\mu_4/\sigma^4$, con los momentos centrales
  obtenidos de los ordinarios:
  $\mu_3 = E[Y^3] - 3E[Y]E[Y^2] + 2E[Y]^3$,
  $\mu_4 = E[Y^4] - 4E[Y]E[Y^3] + 6E[Y]^2E[Y^2] - 3E[Y]^4$.
- Cuantiles $Q(a) = \min\{y : F(y) \ge a\}$ para $a \in \{0{,}05;\ 0{,}25;\ 0{,}5;\ 0{,}75;\
  0{,}95;\ 0{,}995\}$.
- $\text{VaR}_{99{,}5\%} = Q(0{,}995)$ y
  $\text{TVaR}_{99{,}5\%} = \frac{1}{1 - a}\int_a^1 Q(u)\,du$ con $a = 0{,}995$, calculado
  sobre la distribución discreta (válido con átomos).

**Gráficas.** Función de masa $P(Y = y)$ en barras (escala de probabilidad lineal o
logarítmica) y función de distribución $F(y)$ escalonada, ambas con marcas en $E[Y]$ y en
$\text{VaR}_{99{,}5\%}$.

**Comprobaciones** (automatizadas, §9): la suma de las probabilidades es 1 (el motor la
devuelve con cada cálculo) y $E[Y]$ coincide con la valoración pago a pago,

$${}_{k\mid}\ddot a^{(m)}_{x:\overline{n}|} = \sum_{j=0}^{N-1} \frac{v^{k+j/m}}{m}\,{}_{k+j/m}p_x,\qquad
{}_{k\mid}a^{(m)}_{x:\overline{n}|} = \sum_{j=1}^{N} \frac{v^{k+j/m}}{m}\,{}_{k+j/m}p_x ,$$

multiplicada por $C$.

## 9. Implementación y equivalencia numérica

| Capa | Python | JavaScript |
| --- | --- | --- |
| Datos y catálogo | `datos.py` | `data.js` |
| Tablas y modelos | `tablas.py`, `modelos.py` | `engine.js` |
| Rentas | `rentas.py` | `rentas.js` |

Los dos motores deben coincidir con tolerancia $10^{-8}$ (relativa si el valor supera 1).
Todo cambio de cálculo se hace en ambos. Diferencias máximas medidas por la prueba de
paridad: 0 en los datos y valores iniciales; $\sim 10^{-15}$ en $q$, $l$, probabilidades,
esperanzas y $\mu$ (tablas y modelos); $\sim 10^{-11}$ en rentas (momentos de orden alto).

**Función $\Phi$ (Thiele).** Python usa `math.erf`. JavaScript no la trae, así que
`engine.js` calcula $\operatorname{erfc}$ con precisión de doble: serie de Taylor de
$\operatorname{erf}$ para $|x| < 3$ y fracción continua de Laplace (algoritmo de Lentz) para
$|x| \ge 3$. Sustituye a la aproximación de la versión 1.0 (error $\sim 10^{-7}$ y un salto
de $\Phi$ en $x = c$).

**Tests automáticos.** `python tests/ejecutar_tests.py` lanza `pytest` sobre el motor Python
y `node --test` sobre el web. Comprueban, en rejillas de casos de todas las tablas, sexos,
hipótesis de interpolación, modelos y rentas:

- datos de las tablas frente al BOE (§2), con las tolerancias indicadas allí;
- $l_0 = 100\,000$, $l$ no creciente, $l_{y+1} = l_y(1 - q_y)$, $q_{120} = 1$, $l_{121} = 0$;
- identidad de control (§6) y $_n p_x + {}_n q_x = 1$, con tolerancia $10^{-12}$;
- interpolación (§5): $_s p_y$ según la hipótesis y $\mu_a = -\,d\ln l_a/da$ numérica;
- $\mathring e_x$ frente a integración numérica de $l$ y, con UDD y $x$ entera,
  $\mathring e_x = e_x + \tfrac12$ exactamente; error si $l_x = 0$;
- modelos continuos: $S(0) = 1$, $S$ no creciente y $\mu = H'$ (coherencia de las fórmulas
  del §7.1); Heligman–Pollard frente a su definición;
- rentas: probabilidades $\ge 0$ que suman 1, valores crecientes, $E[Y]$ igual a la
  valoración pago a pago (§8.3) con tolerancia $10^{-12}$, coherencia de varianza,
  cuantiles, VaR y TVaR, y validación de parámetros;
- paridad Python/JS de todo lo anterior y de los mensajes de validación.

## 10. Hipótesis y limitaciones

- Los valores del BOE están redondeados: diferencias en el último decimal frente a otras
  implementaciones son esperadas.
- PER2020 generacionales y PASEM2020 estáticas: a las segundas no se les aplica mejora ni
  tiene sentido compararlas por generaciones.
- $\omega = 121$ en todas las tablas y en Heligman–Pollard. En los modelos continuos,
  $l_x$ es positiva más allá de 121; las curvas se dibujan hasta 121.
- Rentas: edad entera, tipo de interés constante, una sola cabeza, interpolación UDD fija.
- Todo se calcula sobre una cabeza; no hay aún estados de grupo.

## 11. Historial de la nota

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0 | 2026-10-07 | Primera versión: tablas, modelos paramétricos, comparación y rentas actuariales. |
| 1.1 | 2026-10-07 | Fase 1. PER2020 Individual de 1er orden tomada tal cual del anexo 2.1 (§3.3); tolerancias del cotejo con el BOE (§2); error en rentas si $l_x = 0$ (§8.1); $\operatorname{erfc}$ de precisión doble en JS y tests automáticos (§9). |

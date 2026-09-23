---
name: calculadora-supervivencia
description: Calcula y representa probabilidades actuariales de supervivencia y fallecimiento (ₙpₓ, ₙqₓ, ₘ|ₙqₓ, eₓ, ₜpₓ con edades no enteras) a partir de las tablas PER2020 y PASEM2020 de la DGSFP o de leyes paramétricas de mortalidad (exponencial, De Moivre, Gompertz, Makeham, Weibull, Perks, Kannisto, Thiele, Siler, Heligman–Pollard), construyendo siempre la función lₓ. Úsala para crear, ampliar o revisar la calculadora (artifact web o app de escritorio Python), añadir tablas o modelos, interpolar entre edades o representar supervivencia, distribución y hazard rate.
---

# Calculadora actuarial de supervivencia

Procedimiento para construir o extender una calculadora de probabilidades de
supervivencia y fallecimiento basada en tablas de mortalidad españolas.

## Cuándo usar esta skill

- Calcular $_n p_x$, $_n q_x$, $_{m\mid n} q_x$ o la esperanza de vida $e_x$.
- Añadir una tabla de mortalidad nueva al catálogo.
- Representar gráficamente una curva de supervivencia o la descomposición de un horizonte
  temporal en supervivencia / fallecimiento / fallecimiento diferido.
- Calcular probabilidades con $x$, $n$ o $m$ reales (interpolación lineal o exponencial).
- Evaluar o añadir un modelo paramétrico de mortalidad.
- Dibujar $_t p_x$, $_t q_x$ y $\mu_{x+t}$, o comparar tablas y modelos entre sí.
- Revisar si un cálculo actuarial de este tipo está bien planteado.

## Principio de diseño

**Construir $l_x$ una sola vez y leer posiciones.** Toda probabilidad de este tipo es un
cociente de valores de la función de supervivencia; resolverlas con productorios
$\prod_{k=0}^{n-1}(1-q_{x+k})$ es más lento, acumula error numérico y no permite reutilizar
el vector para la curva ni para la tabla. La tabla $l_x$ es además lo que el enunciado
académico espera ver.

## Procedimiento

### 1. Obtener el vector de mortalidad `q[0..120]`

Según el tipo de tabla:

- **Generacional (PER2020).** Determinar la cohorte $C = \text{año de cálculo} - x$ y
  recorrer la diagonal de la generación:

  $$q_y = \frac{q^{base}_{y}}{1000}\cdot e^{-\lambda_y\,(C+y-2012)}$$

- **Estática (PASEM2020).** $q_y = q^{base}_y/1000$, con año central base 2019.

Acotar cada valor a $[0,1]$ y forzar $q_{120}=1$.

### 2. Construir la función de supervivencia

```
l[0] = 100000
l[y+1] = l[y] * (1 - q[y])        para y = 0..120
```

Resulta un vector de 122 posiciones ($0..121$), con $\omega = 121$ y $l_{121}=0$.
Cualquier lectura fuera de rango devuelve 0.

### 3. Evaluar las probabilidades

| Símbolo | Expresión | Lectura |
|---|---|---|
| $_n p_x$ | $l_{x+n}/l_x$ | $(x)$ llega vivo a $x+n$ |
| $_n q_x$ | $1 - {}_n p_x$ | $(x)$ muere antes de $x+n$ |
| $_{m\mid n} q_x$ | $(l_{x+m}-l_{x+m+n})/l_x$ | $(x)$ muere entre $x+m$ y $x+m+n$ |
| $_m q_x$ | $1 - l_{x+m}/l_x$ | muere antes del diferimiento |
| $_{m+n} p_x$ | $l_{x+m+n}/l_x$ | sobrevive a todo el horizonte |
| $e_x$ | $\sum_{k\ge1} l_{x+k}/l_x$ | esperanza de vida abreviada |

La esperanza de vida completa es $\mathring{e}_x \approx e_x + 1/2$.

**Identidad de control:** $_m q_x + {}_{m\mid n} q_x + {}_{m+n} p_x = 1$. Es la única
partición exacta de la unidad entre estas magnitudes; conviene usarla como test.

### 4. Catálogo de tablas

Fuente única: Resolución DGSFP de 17-12-2020 (**BOE-A-2020-17154**). $q_x$ en tanto por mil,
edades 0 a 120, para hombres y mujeres por separado.

**Segundo orden** (mejor estimación, anexos 1.1–1.3):
PER2020 Individual · PER2020 Colectiva · PASEM2020 General (vida-riesgo) · PASEM2020 Decesos.

**Primer orden** (con recargos, anexo 2.1 y apartado cuarto):

- PER2020: $q^{(1)}_{base} = q^{(2)}_{base}(1-\text{recargo}_q)$ y
  $\lambda^{(1)} = \lambda^{(2)} + \text{recargo}_\lambda$.
- PASEM2020 Rel (anexo 2.2) y Decesos (anexo 2.4): $q^{(2)} \times 1{,}101875$.
- PASEM2020 NoRel (anexo 2.3): $q^{(2)} \times 1{,}155$, acotando a 1000‰.

**Relación Individual–Colectiva (PER2020):** `Ind[x] = Col[x-1]` para $x\in[11,85]$;
coinciden en 0–10 y 97–120; en 86–96 la Individual tiene valores propios tabulados.
Aplica igual a $q_x$, a $\lambda_x$ **y a los dos recargos del anexo 2.1**, que solo están
tabulados para la Colectiva (la Individual tiene además recargos propios en 86–96). Usar
los recargos de la Colectiva en la Individual desvía $_n p_x$ hasta 6·10⁻⁴ hacia los 70
años: es un error fácil de cometer y difícil de ver.

**Verificación frente al BOE:** los anexos 1.1, 1.2, 1.3 y los recargos del 2.1 del código
coinciden casilla por casilla con el PDF. Las tablas de primer orden derivadas difieren
como mucho 0,001 ‰ de las publicadas, por el redondeo a 3 o 4 decimales que el propio BOE
declara en su apartado séptimo; no se "corrigen" forzando cifras.

### 5. Presentación

- **Notación actuarial siempre**, con subíndice antepuesto real ($_n p_x$), en serif
  matemática. Nunca `nPx`.
- Filas de resultado limpias: símbolo, descripción y valor (y porcentaje). **No** añadir la
  fórmula con los $l_x$ sustituidos debajo: el usuario la considera ruido. El
  planteamiento se explica en el Atlas o en la respuesta escrita, no en la interfaz.
- Probabilidades a 6 decimales y formato es-ES (coma decimal).
- **Barra de descomposición**: segmentos coloreados por magnitud. Ofrecer el modo
  partición (las tres suman 1) además del modo comparación. Para que un segmento minúsculo
  siga siendo visible, usar una **escala realzada**: anchura $\propto\sqrt{p}$, con un
  suelo del 7 % para toda probabilidad no nula y el exceso descontado proporcionalmente de
  los segmentos grandes. Mantener también la escala lineal, indicar cuál está activa y
  poner siempre el valor exacto en la leyenda: una escala no lineal sin avisar induce a
  error.
- **Curva de supervivencia**: $_t p_x$ frente a $t$ desde 0 hasta $\omega - x$, con marca
  en $t=n$ y la franja $[m, m+n]$ sombreada — hace visible que $_{m\mid n}q_x$ es la caída
  de la curva en ese tramo.
- **Tabla $l_x$** desplegable (edad, año, $q$ ‰, $l$, $d$) con las edades clave resaltadas.

### 6. Comparación de escenarios

Un escenario es una combinación (tabla, sexo, año de cálculo) evaluada con la misma edad y
el mismo horizonte. Se compara **una dimensión cada vez**:

| Dimensión | Qué varía | Qué se fija |
|---|---|---|
| Tabla | selección múltiple del catálogo | sexo, $x$, $n$, $m$, año |
| Sexo | hombre / mujer | tabla, $x$, $n$, $m$, año |
| Generación | año de nacimiento $C$ | tabla, sexo, $x$, $n$, $m$ |

Al comparar generaciones, todas se evalúan **a la misma edad $x$**: el año de cálculo de
cada una es $C + x$. Solo es aplicable a tablas generacionales; con una tabla estática hay
que decirlo explícitamente en lugar de dibujar curvas superpuestas idénticas.

Presentar una tabla de escenarios con $_n p_x$, $_n q_x$, $_{m\mid n} q_x$ y $e_x$, con la
diferencia con signo frente al escenario de referencia bajo cada valor, y superponer las
curvas de supervivencia con un color por escenario, conservando las marcas del horizonte.

### 7. Validación

Antes de calcular: $x$ real en $[0,120]$; $n, m, t \ge 0$ reales (los no enteros usan la
interpolación elegida, §8; no hay un parámetro $t$ separado: $n$ real cubre ese caso); año entero entre 1900 y 2200 si la tabla es generacional. Avisar si $x+m+n > \omega$, porque a partir de ahí
$l = 0$ y los resultados se saturan.

### 8. Edades no enteras: interpolación dentro del año

$l$ se construye solo en edades enteras. Para una edad real $y+s$, con $y$ entero y
$0<s<1$, se reparte la mortalidad **publicada** de ese año; no se inventan $q_x$ nuevas.

| Hipótesis | $l_{y+s}$ | $_s p_y$ | $\mu_{y+s}$ |
|---|---|---|---|
| Lineal (UDD) | $l_y - s\,(l_y-l_{y+1})$ | $1 - s\,q_y$ | $q_y/(1-s\,q_y)$, crece dentro del año |
| Exponencial (μ constante) | $l_y\,p_y^{\,s}$ | $p_y^{\,s}$ | $-\ln p_y$, escalonada |
| Balducci (solo Atlas) | $\left(\frac{1-s}{l_y}+\frac{s}{l_{y+1}}\right)^{-1}$ | $\frac{p_y}{1-(1-s)q_y}$ | decrece dentro del año |

Luego $_n p_x = l_{x+n}/l_x$ con ambos $l$ interpolados: la fórmula de siempre, también
para $n$ no entero. Si $l_x = 0$ (edad no alcanzada por la ley), no hay probabilidad
definida: mostrar un error, no un número.

La esperanza de vida completa se calcula exactamente como
$\mathring e_x = \frac{1}{l_x}\int_x^{\omega} l_a\,da$, integrando $l$ tramo a tramo con la
hipótesis elegida (no la aproximación $e_x + \tfrac12$).

### 9. Modelos paramétricos

Todo modelo continuo se define por $\mu(x)$ y su integral $H(x)=\int_0^x\mu$; entonces
$S(x)=e^{-H(x)}$ hace el papel de $l_x/l_0$, y se usa **$l_x = 100\,000\cdot S(x)$** con las
mismas fórmulas del §3 (válidas en cualquier edad real, sin interpolar).

| Modelo | $\mu_x$ | Parám. |
|---|---|---|
| Exponencial | $\lambda$ | 1 |
| De Moivre | $1/(\omega-x)$ | 1 |
| Gompertz | $B c^x$ | 2 |
| Makeham | $A + B c^x$ | 3 |
| Weibull | $(\beta/\theta)(x/\theta)^{\beta-1}$ | 2 |
| Perks | $(A+Bc^x)/(1+Dc^x)$ | 4 |
| Kannisto | $a e^{bx}/(1+a e^{bx})$ | 2 |
| Thiele | $a_1e^{-b_1x} + a_2e^{-b_2(x-c)^2/2} + a_3e^{b_3x}$ | 7 |
| Siler | $a_1e^{-b_1x} + a_2 + a_3e^{b_3x}$ | 5 |
| Heligman–Pollard | $q_x/p_x = A^{(x+B)^C} + De^{-E(\ln x-\ln F)^2} + GH^x$ | 8 |

- Usar $H$ en forma cerrada siempre que exista; si no, integración numérica (Simpson).
- **Heligman–Pollard es discreto** (da $q_x$ en edades enteras): se construye $l_x$ como con
  una tabla ($\omega=121$) y las edades no enteras usan la interpolación del §8.
- De Moivre: $l=0$ desde $\omega$; avisar si $x \ge \omega$.
- **Valores iniciales:** no hay parámetros "oficiales". Los de la calculadora salen de un
  ajuste propio por mínimos cuadrados a PASEM2020 General 2º orden, por sexo
  (`ajuste_presets.py`): $S(x)$ para el exponencial; $\ln q_x$ en 30–100 (Gompertz,
  Makeham, Weibull, Perks), 80–100 (Kannisto) y 0–100 (Thiele, Siler, HP). De Moivre se
  fija en $\omega=121$ porque su ajuste diverge. Decirlo siempre en la interfaz.
- Parámetros con rango de varios órdenes de magnitud ($B$, $a$, $A$ de HP…) se mueven en
  **escala logarítmica** en los deslizadores.

### 10. Gráficas

En cada vista, tres paneles en función de $t$ desde 0 hasta $\omega-x$:
supervivencia $_t p_x$, distribución $_t q_x = 1 - {}_t p_x$ y tanto instantáneo
$\mu_{x+t}$ (escala logarítmica por defecto, conmutable a lineal). Conservar la marca en
$t=n$ (con el punto $(n, {}_n p_x)$) y la franja $[m, m+n]$. En la vista paramétrica,
superponer en gris discontinuo la tabla de referencia a la que se ajustaron los valores
iniciales, para ver cómo cambia la forma al mover cada parámetro.

La comparación admite escenarios mixtos (tabla o modelo, cada uno con su sexo): mismas
tres gráficas superpuestas y tabla de valores con la diferencia frente al primero. Los
parámetros de los modelos se editan **dentro de la pestaña de comparación** (cada escenario
se despliega y tiene sus propios parámetros); obligar a cambiar de pestaña para ajustarlos
es incómodo.

### 11. Implementaciones

- **Artifact web**: React + recharts, un único HTML autocontenido (bundle con esbuild).
- **Escritorio**: Python con PySide6 + matplotlib; motor separado de la interfaz
  (`datos.py`, `tablas.py`, `modelos.py`) y .exe con PyInstaller (`calculadora.spec`).
- Ambos motores deben dar el mismo resultado (tolerancia $10^{-8}$): al cambiar uno,
  cambiar el otro y comparar.

## Errores frecuentes

- Olvidar dividir la $q$ entre 1000 (los anexos van en tanto por mil).
- Aplicar el factor de mejora con el año de cálculo en vez de con el año de la cohorte:
  el exponente es $(C+y-2012)$, no $(\text{año}-2012)$.
- Aplicar factor de mejora a las PASEM2020, que son estáticas.
- Presentar $_n p_x$, $_n q_x$ y $_{m\mid n} q_x$ como si repartieran un total: los dos
  primeros suman 1 y el tercero es un suceso que se solapa con ellos.
- Reconstruir la PER Individual desplazando también las edades 0–10 o 97–120, que no se
  desplazan.
- Interpolar o inventar $q_x$ para edades no publicadas.
- Diferencias en el último decimal frente a otras fuentes: vienen del redondeo del BOE y
  no deben "corregirse".
- Confundir interpolar **dentro del año** (repartir una $q_y$ publicada) con inventar una $q$
  para una edad no publicada: lo primero es legítimo y se declara; lo segundo, no.
- Calcular un modelo paramétrico con productorios de $p_x$ discretizados en lugar de leer
  $l_x = 100\,000\cdot S(x)$.
- Presentar los valores iniciales de los parámetros como si fueran valores publicados.

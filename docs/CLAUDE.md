# CLAUDE.md

Contexto y convenciones del proyecto **Modelos de Supervivencia**, la asignatura del
Máster en Ciencias Actuariales y Financieras. Este fichero recoge las instrucciones
permanentes que aplican a **cualquier** trabajo de la asignatura —teoría, ejercicios,
código, gráficos o memorias— y documenta, en su última sección, los trabajos ya
realizados. Claude debe leerlo antes de responder o de escribir código.

* * *

## 1\. Ámbito del proyecto

Este proyecto cubre **toda la asignatura**, no un único trabajo. Dentro de él caben:

- **Teoría**\: dudas conceptuales sobre supervivencia, mortalidad, tablas y estimación.
- **Ejercicios**\: resolución paso a paso, con la notación y las convenciones de este fichero.
- **Código y artifacts**\: calculadoras, simulaciones y utilidades de cálculo.
- **Gráficos**\: curvas de supervivencia, comparativas y representación de probabilidades.
- **Documentación y memorias** de las entregas.

Las secciones 2 a 6 aplican a cualquiera de esas tareas. La sección 7 documenta los
trabajos concretos ya realizados, con sus decisiones propias.

## 2\. Instrucciones permanentes

> **Utilizar notación actuarial** en todo: explicaciones, ejercicios, interfaces y
> documentación.

No es una cuestión estética. En texto, los símbolos llevan sus subíndices reales
(`_n p_x`, `_{m\mid n} q_x`), nunca `nPx` ni `n_p_x`. En código se componen con
subíndice antepuesto y pospuesto y tipografía serif matemática; en la calculadora
existen para eso los componentes `<Sym pre base post />` y `<L a={...} />`, y cualquier
símbolo nuevo debe pasar por ellos.

Además, en cualquier tarea de la asignatura:

- **Mostrar el planteamiento**, no solo el resultado: de qué fórmula se parte y qué
  valores se sustituyen.
- **No inventar ni interpolar** valores de tablas ni parámetros. Si un dato no está
  publicado o no se aporta, decirlo en lugar de rellenarlo. Repartir **dentro del año**
  una `q_y` publicada (interpolación lineal o exponencial para edades no enteras) sí está
  permitido, siempre declarando la hipótesis; lo que no se hace es crear `q_x` nuevas.
- **Declarar los supuestos** que el enunciado no fije: tabla y orden empleados, año de
  cálculo, hipótesis de fraccionamiento de la edad.
- Redactar en **español (es\-ES)**, con coma decimal.

## 3\. Convenciones de cálculo (obligatorias)

Aplican a cualquier cálculo de la asignatura, se haga a mano o en código.

1. **Todo se calcula a partir de `l_x`.** Nada de productorios `\prod(1-q_{x+k})` ni de
   sumatorios acumulados: se construye una única vez el vector `l` y se leen posiciones.
   
   ```math
   l_0 = 100\,000,\qquad l_{y+1} = l_y\,(1-q_y),\qquad \omega = 121 \ (q_{120}=1,\ l_{121}=0)
   ```

2. **Fórmulas cerradas sobre `l`\:**
   
   ```math
   _n p_x = \frac{l_{x+n}}{l_x},\qquad
     _n q_x = 1 - {}_n p_x,\qquad
     _{m\mid n} q_x = \frac{l_{x+m}-l_{x+m+n}}{l_x}
   ```
   
   ```math
   \mathring{e}_x \approx e_x + \tfrac12,\qquad e_x = \sum_{k\ge 1} \frac{l_{x+k}}{l_x}
   ```

3. **Tablas generacionales (PER2020).** Se sigue la diagonal de la cohorte nacida en
   `C = \text{año} - x`, aplicando el factor de mejora sobre la `q` base de 2012:
   
   ```math
   q_{y,\,C+y} = q_{y,\,2012}\cdot e^{-\lambda_y\,(C+y-2012)}
   ```

4. **Tablas estáticas (PASEM2020).** Año central base 2019; la `q` se usa tal cual, sin
   factor de mejora.

5. Las `q_x` publicadas están **en tanto por mil**\: dividir entre 1000 al usarlas y
   acotar el resultado a `[0,1]`.

**Identidad de control:** `_m q_x + {}_{m\mid n} q_x + {}_{m+n} p_x = 1`. Es la única
partición exacta de la unidad entre estas magnitudes, y sirve para verificar cualquier
resultado.

## 4\. Fuentes de datos

Salvo que un enunciado indique otra cosa, las tablas de la asignatura son las oficiales
españolas de la Resolución de la DGSFP de 17 de diciembre de 2020, **BOE\-A\-2020\-17154**\:

- Anexo 1.1 — PER2020 Individual y Colectiva, 2º orden (`q_x` base 2012 y `\lambda_x`).
- Anexo 1.2 — PASEM2020 General (vida\-riesgo), 2º orden.
- Anexo 1.3 — PASEM2020 Decesos, 2º orden.
- Anexo 2.1 — recargos técnicos y tablas PER2020 de primer orden (Colectiva e Individual).
- Anexos 2.2, 2.3 y 2.4 — PASEM2020 de primer orden: Rel, NoRel y Decesos.

Los datos del código se han cotejado casilla por casilla con el PDF del BOE: los anexos
1.1, 1.2, 1.3 y los recargos del 2.1 coinciden exactamente. Las tablas de primer orden que
el código deriva difieren del BOE como mucho en 0,001 ‰, por el redondeo a 3 o 4 decimales
con que se publican (el propio BOE advierte de ello en su apartado séptimo).

Derivaciones ya establecidas, que **no deben reinventarse**\:

- **PER Individual desde Colectiva:** `Ind[x] = Col[x-1]` para `x\in[11,85]`; idénticas en
  0–10 y 97–120; valores propios tabulados en 86–96.
- **PER 1er orden:** `q^{(1)}_{base} = q^{(2)}_{base}\,(1-\text{recargo}_q)` y
  `\lambda^{(1)} = \lambda^{(2)} + \text{recargo}_\lambda`. **Los recargos del anexo 2.1
  están tabulados para la Colectiva**; los de la Individual siguen el mismo desfase de un
  año (`Ind[x] = Col[x-1]` en 11–85) y tienen valores propios en 86–96. Aplicar los de la
  Colectiva a la Individual desvía `_n p_x` hasta 6·10⁻⁴ en torno a los 70 años.
- **PASEM 1er orden:** Rel (vida\-riesgo vinculado, anexo 2.2) y Decesos (anexo 2.4)
  `\times 1{,}101875`; NoRel (resto de vida\-riesgo, anexo 2.3) `\times 1{,}155`.

## 5\. Convenciones para el código y los artifacts

- Artifact **React** con **recharts** como única dependencia externa para gráficos. Puede
  ser un único `.jsx` (§7.1) o, si crece, varios módulos empaquetados con esbuild en un
  único HTML autocontenido (§7.2).
- Versión de escritorio en **Python**: PySide6 + matplotlib, motor separado de la
  interfaz, y `.exe` con PyInstaller. El motor Python y el JavaScript deben dar los mismos
  números (tolerancia `10^{-8}`).
- Estado con `useState`; los cálculos derivados, memorizados con `useMemo`.
- **Datos separados de la interfaz.** El bloque de datos numéricos va delimitado por
  `// @@DATA_START` y `// @@DATA_END`\: al editar la interfaz no se toca ese bloque, y al
  corregir datos no se toca la interfaz.
- **Validar antes de calcular:** `x` en `[0,120]`; `n, m \ge 0`; año entero entre
  1900 y 2200 en tablas generacionales. En §7.1 las edades son enteras; desde §7.2 se
  admiten reales y se tratan con la interpolación elegida. Avisar explícitamente cuando
  `x+m+n > \omega`, y mostrar un error (no un resultado) cuando `l_x = 0`, porque entonces
  las probabilidades condicionadas a `(x)` no están definidas.
- En la calculadora de §7.1, junto a cada resultado se muestra la fórmula con los `l_x`
  sustituidos. **Desde §7.2 no**: a petición propia, las filas de resultado llevan solo
  símbolo, descripción y valor, porque las fórmulas sustituidas añadían ruido. En
  ejercicios y explicaciones escritas se sigue mostrando el planteamiento (§2).
- Idioma **es\-ES** en todo: textos, coma decimal, `toLocaleString("es-ES")`.
  Probabilidades a 6 decimales; `l_x` a 2.
- Tipografía: serif matemática (STIX Two Text) para símbolos y cifras de resultado,
  sans (Public Sans) para el resto.
- Accesibilidad: `aria-pressed` en los controles segmentados, `aria-label` descriptivo en
  los gráficos, `role="alert"` en los errores, y respeto a `prefers-reduced-motion`.

## 6\. Advertencias

- Los valores del BOE están redondeados: pueden aparecer diferencias en el último decimal
  frente a otras implementaciones. Es esperado; no se "corrige" forzando cifras.
- `_n p_x + {}_n q_x = 1`, pero `_{m\mid n}q_x` **no** forma parte de esa partición: se
  solapa con las otras dos. Cualquier gráfico o explicación debe dejarlo claro para no
  inducir a error.
- Las PER2020 son generacionales y las PASEM2020 estáticas: no aplicar factor de mejora a
  estas últimas, ni comparar generaciones con ellas.
- Nunca inventar valores de `q_x` ni interpolar edades que no estén publicadas.

## 7\. Trabajos de la asignatura

### 7\.1 Calculadora de supervivencia y fallecimiento

Artifact interactivo que calcula, dados la edad `x`, el plazo `n`, el diferimiento `m`,
la tabla, el sexo y —en tablas generacionales— el año de cálculo:

| Magnitud | Significado |
| --- | --- |
| `_n p_x` | probabilidad de que `(x)` sobreviva `n` años |
| `_n q_x` | probabilidad de que `(x)` fallezca dentro de los próximos `n` años |
| `_{m\mid n} q_x` | probabilidad de que `(x)` fallezca entre las edades `x+m` y `x+m+n` |

Más la esperanza de vida `e_x`. Catálogo de nueve tablas (PER2020 Individual y Colectiva,
PASEM2020 General y Decesos, en 2º y 1er orden).

**Interfaz.** Panel de parámetros a la izquierda (fijo, agrupado en bloques: Colectivo,
Edad y horizonte, Generación) y resultados a la derecha, en dos pestañas: *Cálculo* y
*Comparación*. En la vista de cálculo, una fila por probabilidad con su color de acento
—verde supervivencia, granate fallecimiento, ocre diferido—, la fórmula con los `l_x`
sustituidos y el valor a 6 decimales; al pie, la esperanza de vida. Debajo, la tabla
`l_x` desplegable con las edades clave resaltadas.

**Gráficos.** *Descomposición en el horizonte*\: barra segmentada, con dos modos de
contenido (las tres probabilidades, o la partición de la unidad) y dos escalas —realzada,
con anchura `\propto\sqrt{p}` y un mínimo visible del 7 %, y lineal, con anchura
`\propto p`—. La realzada evita que las probabilidades pequeñas resulten invisibles; el
valor exacto va siempre en la leyenda y el pie indica qué escala está activa.
*Curva de supervivencia*\: `_t p_x` frente a `t`, con línea de referencia en `t=n` y la
franja `[m, m+n]` sombreada, para que se vea que `_{m\mid n}q_x` es la caída de la curva
en esa franja.

**Comparación.** Tres dimensiones, excluyentes entre sí:

- **Tabla** — selección múltiple del catálogo, con sexo, edad y horizonte fijos.
- **Sexo** — hombre frente a mujer con la misma tabla y parámetros.
- **Generación** — varios años de nacimiento (hasta 6), evaluados todos **a la misma edad
  `x`**, de modo que el año de cálculo de cada uno es `\text{nacimiento}+x`. Solo tiene
  sentido con tablas PER2020: con una PASEM2020 hay que avisar de que son estáticas, en
  lugar de dibujar curvas idénticas.

Se presenta como tabla de escenarios con `_n p_x`, `_n q_x`, `_{m\mid n}q_x` y `e_x`,
con la diferencia con signo frente al escenario de referencia bajo cada valor, y
superposición de las curvas de supervivencia con un color por escenario.

### 7\.2 Calculadora de supervivencia v2: tablas, modelos paramétricos, comparación y atlas

Aplicación nueva (no deriva del código de §7.1) entregada en dos formas equivalentes:
artifact web (`calculadora_supervivencia.html`) y aplicación de escritorio Python con
generación de `.exe`. Cuatro pestañas; en todas, parámetros a la izquierda y resultados a
la derecha.

**1. Tablas de mortalidad.** Las nueve tablas de §7.1, organizadas en el desplegable por
tipo y uso: *generacionales · supervivencia* (PER2020 Individual y Colectiva),
*estáticas · riesgo* (PASEM2020 General, Rel y NoRel) y *estáticas · decesos* (PASEM2020
Decesos). Calcula `_n p_x`, `_n q_x`, `_{m\mid n} q_x`, `e_x` y `\mathring e_x` con `x`,
`n` y `m` **reales**. No hay un parámetro `t` aparte: el plazo `n` ya admite decimales
(p. ej. `_{2,5}p_{45}`) y todos los resultados salen en el mismo bloque. Interpolación
seleccionable para las edades no enteras:

```math
\text{lineal: } {}_s p_y = 1 - s\,q_y \quad (l_{y+s} = l_y - s\,d_y) \qquad
\text{exponencial: } {}_s p_y = p_y^{\,s} \quad (l_{y+s} = l_y\,p_y^{\,s})
```

`\mathring e_x` se obtiene integrando `l` tramo a tramo con la misma hipótesis.

**2. Modelos paramétricos.** Exponencial, De Moivre, Gompertz, Makeham, Weibull, Perks,
Kannisto, Thiele, Siler y Heligman–Pollard. Los continuos dan `S(x) = e^{-H(x)}` y se usa
`l_x = 100\,000\cdot S(x)`; Heligman–Pollard da `q_x` enteras y se trata como una tabla.
Cada parámetro tiene deslizador (logarítmico si abarca varios órdenes de magnitud) y
campo numérico; la tabla PASEM2020 General 2º orden se superpone en gris como referencia.

*Decisión propia:* los valores iniciales **no son publicados**; salen de un ajuste por
mínimos cuadrados a PASEM2020 General 2º orden por sexo (`ajuste_presets.py`). De Moivre
se fija en `\omega = 121` porque su ajuste diverge. Se indica en la interfaz.

**3. Comparación.** Hasta 8 escenarios mixtos (tabla o modelo, cada uno con su sexo), con
tabla de valores y diferencias frente al primero, y las tres gráficas superpuestas. Los
parámetros de cada modelo se ajustan **en la propia pestaña** (desplegando el escenario):
cada escenario guarda sus propios parámetros, copiados de la pestaña Modelos paramétricos
al añadirlo, de modo que se pueden comparar dos versiones del mismo modelo. Si un modelo
se repite, se numera (`Gompertz (1)`, `Gompertz (2)`).

**4. Atlas.** *Paramétrico*: tabla-resumen (parámetros, forma de `\mu`, tramo de edades,
limitación principal) y ficha por modelo con miniatura de `\log\mu`, usos, desventajas y
relaciones. *No paramétrico*: paso de la tabla a `l_x`, hipótesis de interpolación
(lineal, exponencial y Balducci como referencia) y ficha de cada familia de tablas.

**Gráficas.** Tres paneles en cada vista: `_t p_x`, `_t q_x` y `\mu_{x+t}` (log/lineal),
con marca y punto en `t=n` y franja `[m,m+n]`. Los textos de la interfaz
evitan fórmulas largas: el detalle matemático va en el Atlas.

**Ficheros Python.** `datos.py` (datos y catálogo), `tablas.py` y `modelos.py` (motores),
`presets_data.py` (generado), `ajuste_presets.py`, `atlas.py`, `app.py` (interfaz),
`calculadora.spec` y `build_exe.bat` (`.exe`), `requirements.txt`, `README.md`.

### 7\.3 Trabajos posteriores

Se documentan aquí a medida que se hagan, con el mismo esquema: objetivo, magnitudes o
métodos empleados, y las decisiones propias que no se deduzcan de las secciones 2 a 6.

# CLAUDE.md

Convenciones técnicas, decisiones y estado de la **Calculadora de supervivencia**, una
herramienta actuarial orientada a uso profesional. Claude debe leer este fichero antes de
escribir código o documentación del proyecto. El espacio de trabajo completo (apuntes,
ejecutables) se describe en el `CLAUDE.md` de la carpeta superior, fuera de este repo.

> Este repositorio es **público**. No incluir apuntes, enunciados ni material de terceros.

* * *

## 1\. Principios

- **Rigor antes que comodidad.** Cada resultado debe poder trazarse a una fuente publicada
  o a una hipótesis declarada en la interfaz.
- **No inventar datos.** Si una `q_x` o un parámetro no está publicado ni aportado, se dice;
  no se rellena. Repartir **dentro del año** una `q_y` publicada (lineal o exponencial) sí
  está permitido declarando la hipótesis; crear `q_x` nuevas, no.
- **Declarar supuestos**: tabla y orden, año de cálculo, hipótesis de fraccionamiento,
  tipo de interés.
- **Notación actuarial** en interfaz y documentación: subíndices reales (`_n p_x`,
  `_{m\mid n} q_x`), nunca `nPx` ni `n_p_x`. En la web, mediante `<Sym pre base post />` y
  `<L a={...} />`; cualquier símbolo nuevo pasa por ellos.
- Idioma **es\-ES**, coma decimal.

## 2\. Convenciones de cálculo (obligatorias)

1. **Todo se calcula a partir de `l_x`.** Nada de productorios ni sumatorios acumulados:
   se construye una vez el vector `l` y se leen posiciones.

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

   `\mathring e_x` se obtiene integrando `l` tramo a tramo con la hipótesis de interpolación
   activa.

3. **Edades no enteras** (interpolación seleccionable):

   ```math
   \text{lineal (UDD): } {}_s p_y = 1 - s\,q_y \quad (l_{y+s} = l_y - s\,d_y) \qquad
   \text{exponencial: } {}_s p_y = p_y^{\,s} \quad (l_{y+s} = l_y\,p_y^{\,s})
   ```

4. **Tablas generacionales (PER2020).** Diagonal de la cohorte `C = \text{año} - x`, con
   factor de mejora sobre la `q` base de 2012:

   ```math
   q_{y,\,C+y} = q_{y,\,2012}\cdot e^{-\lambda_y\,(C+y-2012)}
   ```

5. **Tablas estáticas (PASEM2020).** Año central base 2019; `q` tal cual, sin mejora.
6. Las `q_x` publicadas están **en tanto por mil**: dividir entre 1000 y acotar a `[0,1]`.
7. **Modelos continuos:** `l_x = 100\,000\cdot S(x)`, `S(x) = e^{-H(x)}`.
   Heligman–Pollard da `q_x` enteras y se trata como una tabla.

**Identidad de control:** `_m q_x + {}_{m\mid n} q_x + {}_{m+n} p_x = 1`.

### 2\.1 Rentas actuariales

Con `v = (1+I)^{-1}`, `N = m\cdot n` plazos y, en la vitalicia, `n = w + 1 - x - k`
(`w = 120`). La renta se trata como variable aleatoria: se construye su distribución
(valores y probabilidades leídas de `l_x`) y de ella salen los momentos
`E[Y^s] = \sum \text{valor}^s\cdot\text{prob}`, la prima pura única, varianza, desviación,
CV, asimetría, curtosis, cuantiles, VaR y TVaR al 99,5 %. `x` entera; `n` y `k`, múltiplos
de `1/m`; las edades `x + j/m` usan UDD. El detalle de valores y probabilidades de la
prepagable y la postpagable está en el `README.md`.

## 3\. Fuentes de datos

Resolución de la DGSFP de 17 de diciembre de 2020, **BOE\-A\-2020\-17154**:

- Anexo 1.1: PER2020 Individual y Colectiva, 2º orden (`q_x` base 2012 y `\lambda_x`).
- Anexo 1.2: PASEM2020 General (vida\-riesgo), 2º orden.
- Anexo 1.3: PASEM2020 Decesos, 2º orden.
- Anexo 2.1: recargos técnicos y PER2020 de primer orden.
- Anexos 2.2, 2.3 y 2.4: PASEM2020 de primer orden (Rel, NoRel y Decesos).

`python/verificacion_boe.py` coteja casilla por casilla con `boe_anexos.json` (y es parte
de los tests): los anexos 1.1, 1.2, 1.3, los recargos del 2.1 y la PER Individual de 1er
orden coinciden exactamente; las de primer orden derivadas difieren como mucho 0,001 ‰ en
`q` y una unidad del 4º decimal en `\lambda` por el redondeo del BOE (su apartado séptimo
lo advierte). Esas son las tolerancias del cotejo.

Derivaciones establecidas, que **no deben reinventarse**:

- **PER Individual desde Colectiva:** `Ind[x] = Col[x-1]` en `[11,85]`; idénticas en 0–10
  y 97–120; valores propios en 86–96.
- **PER Colectiva 1er orden:** `q^{(1)}_{base} = q^{(2)}_{base}(1-\text{recargo}_q)`,
  `\lambda^{(1)} = \lambda^{(2)} + \text{recargo}_\lambda` (recargos del anexo 2.1).
- **PER Individual 1er orden: tal cual del anexo 2.1** (`PER_IND1_*`), sin derivar. Sus
  recargos en 86–96 no se publican; reconstruirlos desviaba `_n p_x` hasta 8,6·10⁻⁴ y usar
  los de la Colectiva, hasta 6·10⁻⁴. Decidido el 2026-10-07 (fase 1).
- **PASEM 1er orden:** Rel y Decesos `\times 1{,}101875`; NoRel `\times 1{,}155`.

## 4\. Arquitectura y convenciones de código

Dos implementaciones equivalentes, con el **motor separado de la interfaz**:

| Capa | Python (`python/`) | Web (`web/src/`) |
| --- | --- | --- |
| Datos y catálogo | `datos.py` | `data.js` |
| Motor de tablas y modelos | `tablas.py`, `modelos.py` | `engine.js` |
| Rentas | `rentas.py` | `rentas.js` |
| Interfaz | `app.py` (PySide6 + matplotlib) | `App.jsx`, `rentas.jsx` (React + recharts) |
| Atlas | `atlas.py` | `atlas.jsx` |

- Los dos motores deben dar los mismos números (tolerancia `10^{-8}`; diferencia medida
  ~10⁻¹⁵ en tablas y modelos, ~10⁻¹¹ en rentas). Todo cambio de cálculo se hace **en
  ambos**, y la prueba de paridad (`tests/python/test_paridad.py`) lo comprueba.
- JS no tiene `Math.erf`: `engine.js` implementa `erfc` con precisión de doble (Taylor +
  fracción continua). No volver a aproximaciones de ~10⁻⁷.
- **Tests** (`tests/`): `python tests/ejecutar_tests.py` ejecuta `pytest tests/python` y
  `node --test tests/js/*.test.mjs` (también `npm test` en `web/`). Requiere `pytest`
  (`requirements.txt`) y Node ≥ 20. Las rejillas de casos están en `tests/python/casos.py`;
  `tests/js/volcado.mjs` expone el motor web a la prueba de paridad. Todo cálculo nuevo
  llega con sus tests (identidades, comprobación independiente y paridad).
- `web/package.json` tiene `"type": "module"` para que Node importe `web/src/` directamente.
- Bloque de datos numéricos delimitado por `// @@DATA_START` y `// @@DATA_END`: al tocar
  la interfaz no se toca ese bloque, y viceversa.
- Web: recharts como única dependencia de gráficos; esbuild empaqueta en un HTML
  autocontenido (`web/calculadora_supervivencia.html`), que se copia a `index.html` para
  GitHub Pages. Estado con `useState`, derivados con `useMemo`.
- Escritorio: `.exe` con PyInstaller (`build_exe.bat`, `calculadora.spec`); el resultado
  se mueve a la carpeta `ejecutables/` del espacio de trabajo, fuera del repo.
- **Validar antes de calcular:** `x\in[0,120]`; `n, m \ge 0`; año entero en `[1900, 2200]`
  en generacionales. Avisar si `x+m+n > \omega`; error (no resultado) si `l_x = 0`.
- Presentación: probabilidades a 6 decimales, `l_x` a 2, `toLocaleString("es-ES")`.
  Filas de resultado con símbolo, descripción y valor, sin fórmula sustituida.
  Tipografía serif matemática (STIX Two Text) para símbolos y cifras; Public Sans para
  el resto. Parámetros a la izquierda, resultados a la derecha.
- Accesibilidad: `aria-pressed` en controles segmentados, `aria-label` en gráficos,
  `role="alert"` en errores, respeto a `prefers-reduced-motion`.

## 5\. Advertencias

- Los valores del BOE están redondeados; diferencias en el último decimal son esperadas.
- `_n p_x + {}_n q_x = 1`, pero `_{m\mid n}q_x` **no** forma parte de esa partición.
- PER2020 generacionales, PASEM2020 estáticas: no aplicar mejora a estas ni comparar
  generaciones con ellas.
- Los valores iniciales de los modelos paramétricos **no son publicados**: ajuste propio
  por mínimos cuadrados a PASEM2020 General 2º orden por sexo (`ajuste_presets.py`).
  De Moivre fijado en `\omega = 121` porque su ajuste diverge. Se indica en la interfaz.

## 6\. Estado actual

Cinco pestañas, en web y escritorio:

1. **Tablas de mortalidad**: nueve tablas (PER2020 Individual y Colectiva; PASEM2020
   General, Rel, NoRel y Decesos; 2º y 1er orden). `_n p_x`, `_n q_x`, `_{m\mid n} q_x`,
   `e_x`, `\mathring e_x` con `x`, `n`, `m` reales.
2. **Modelos paramétricos**: exponencial, De Moivre, Gompertz, Makeham, Weibull, Perks,
   Kannisto, Thiele, Siler, Heligman–Pollard; deslizador (log si procede) y campo por
   parámetro, con PASEM2020 General de referencia.
3. **Comparación**: hasta 8 escenarios mixtos, cada uno con sexo y parámetros propios;
   modelos repetidos se numeran.
4. **Rentas actuariales**: temporal o vitalicia, pre o postpagable, `m` pagos al año,
   diferimiento `k`, interés `I`; distribución, momentos y métricas de riesgo (§2.1).
5. **Atlas**: guía de modelos paramétricos y de tablas e hipótesis de interpolación.

Gráficas en las tres primeras: `_t p_x`, `_t q_x` y `\mu_{x+t}` (log/lineal), con marca en
`t=n` y franja `[m,m+n]`.

**Base de calidad (fase 1, cerrada):** batería de tests automáticos en `tests/` (≈340 en
Python con paridad incluida, ≈170 en JS; ~1 min). Detalle en `docs/NOTA_TECNICA.md` §9.

### 6\.1 Flujo de trabajo para cada cambio

Toda nueva funcionalidad o corrección sigue estos pasos, en este orden:

1. **Contexto**: leer este fichero, el `CHANGELOG.md` y, si aplica, los apuntes aportados
   en `apuntes/`.
2. **¿Está en la hoja de ruta?** Si Antonio pide algo que no está en §7, antes de
   programar: proponer en qué capa (§7.1) y en qué fase encaja, o si va como mejora
   suelta; avisar si depende de algo aún no hecho; y, con su visto bueno, **añadirlo a §7**
   (fase, lista de espera o mejoras sueltas). La hoja de ruta siempre refleja lo acordado.
3. **Plan breve**: qué se cambia, en qué capas y ficheros, qué fórmulas; si hay una
   decisión de criterio actuarial, preguntar a Antonio antes de programar.
4. **Implementar en ambos motores** (Python y JS) y en ambas interfaces.
5. **Verificar**: `python tests/ejecutar_tests.py` en verde (añadiendo los tests del cambio:
   identidades, comprobación independiente y paridad) y comprobación visual de la interfaz.
6. **Documentar en el mismo commit**:
   - `docs/NOTA_TECNICA.md`: toda fórmula, hipótesis, dato o magnitud nueva o cambiada;
     subir versión y añadir línea en su historial (§11). **Obligatorio** si cambia algún
     cálculo; una corrección solo de interfaz no lo requiere.
   - `CHANGELOG.md`: entrada con fecha.
   - Este fichero: §6 (estado), §7 (hoja de ruta) y §8 si procede de una asignatura.
   - `README.md` si cambia lo que la calculadora calcula.
7. **Compilar, siempre las dos** (petición de Antonio, sin esperar a que lo pida): web
   (`node build.mjs` en `web/` y copiar el HTML a `index.html`, en el mismo commit) y el `.exe`
   (`python -m PyInstaller --noconfirm --clean calculadora.spec` en `python/`; `build_exe.bat`
   hace lo mismo pero se queda en `pause`). Mover `dist/CalculadoraSupervivencia.exe` a
   `ejecutables/` y borrar `build/` y `dist/`.
8. **Commit** con mensaje descriptivo. **Push solo cuando Antonio lo pida.**

## 7\. Hoja de ruta

Acordada el 2026-10-07. Criterio: **no ir por delante de lo que Antonio ha estudiado**;
lo que aún no ha visto queda en la lista de espera. Se mantienen las dos plataformas en
paridad: cada fase se cierra cuando funciona en ambas y pasa los tests.

### 7\.1 Arquitectura objetivo del motor (cuatro capas)

1. **Mortalidad → `l_x`**: tablas y modelos (existe).
2. **Estado**: sobre qué se mide la supervivencia: `(x)`, vida conjunta (disolución con
   la primera muerte) o último superviviente (extinción con la última). Cada estado da su
   `_t p` a partir de las `l_x` individuales.
3. **Producto**: qué se paga, cuándo y condicionado a qué (supervivencia o fallecimiento).
   Rentas y seguros son productos; el mixto es la suma de dos.
4. **Descuento**: función `v(t)`. Hoy `(1+I)^{-t}` con `I` constante.

Cada contenido nuevo es una pieza en una capa, sin rehacer las demás.

### 7\.2 Fases

| Fase | Línea | Contenido |
| --- | --- | --- |
| 1 | **Base de calidad** | Tests automáticos (pytest y node): paridad Python/JS, identidad de control, suma de probabilidades = 1, `verificacion_boe.py` integrado. Script único. |
| 2 | **Seguros sobre una cabeza** | Temporal a `n` años, vida entera, capital diferido, mixto (diferido + temporal) y seguro diferido de fallecimiento. Como en rentas: distribución completa de la v.a. del valor actual, momentos, prima pura única y métricas de riesgo. Se separan las capas de producto y descuento. Además: (a) gráfica de la **función de densidad de la vida residual** $f_{T(x)}(t) = {}_t p_x\,\mu_{x+t}$ junto a supervivencia, distribución y tanto instantáneo (pestañas de tablas, modelos y comparación), y funciones de masa y distribución también en seguros (en rentas ya existen); (b) preset del **tipo de interés técnico** del año (§7.3); (c) **recargo de seguridad** libre, en rentas y seguros: campo `α` (%) elegido por el usuario, prima recargada `(1+\alpha)\,E[Z]`, mostrando prima pura, importe del recargo y prima recargada. No se impone ningún principio de cálculo de primas. |
| 3 | **Probabilidades de grupo** | Vida conjunta (disolución) y último superviviente (extinción) para dos o más cabezas, cada una con su tabla y sexo. Se crea la capa de estado. |
| 4 | **Carteras y exportación** | Cargar una BBDD de asegurados, valorar en lote; exportar a Excel y PDF. |

**Fase activa: 2.** Las decisiones de diseño de cada fase se anotan aquí al cerrarla.

**Fase 1, cerrada el 2026-10-07.** Decisiones:

- `pytest` para Python y el ejecutor nativo `node --test` para JS (sin dependencias nuevas);
  script único `tests/ejecutar_tests.py`.
- Paridad: Python genera los casos, Node los calcula con el motor web y se comparan con
  tolerancia `10^{-8}` relativa. Identidades con `10^{-12}`.
- Tolerancias del cotejo con el BOE: 0,001 ‰ en `q` y `10^{-4}` en `\lambda` para las tablas
  de 1er orden que se derivan; exactas el resto.
- Correcciones que destaparon los tests: PER Individual de 1er orden tomada del BOE (§3);
  error en rentas si `l_x = 0` (antes, división por cero en Python y NaN en la web);
  `e_x` = NaN si `l_x = 0` también en la web; `erfc` de precisión doble en JS.

### 7\.3 Tipo de interés técnico

Fuente: resolución anual de la DGSFP "por la que se publica el tipo de interés máximo a
utilizar en el cálculo contable de la provisión de seguros de vida", en el BOE de enero,
en aplicación del art. 33 del ROSSP (RD 2486/1998). **2026: 1,95 %**
(Resolución de 9 de enero de 2026, BOE-A-2026-1226). La calculadora lo ofrecerá como valor
por defecto, con año y referencia visibles y editable. Se actualiza cada enero.

### 7\.4 Lista de espera (cuando se estudie)

- Rentas y seguros sobre grupos (se apoyarán en las fases 2 y 3).
- Primas periódicas, reservas matemáticas, curva de tipos EIOPA.

### 7\.5 Mejoras sueltas

Peticiones nuevas que no pertenecen a ninguna fase. Se añaden aquí al acordarlas y se
tachan al implementarlas, con referencia a su entrada del `CHANGELOG.md`.

*(ninguna todavía)*

## 8\. Incorporaciones desde asignaturas

Cuando una mejora proceda de material de clase (guardado en `apuntes/`, fuera del repo),
anotar aquí: asignatura, qué se incorpora y qué decisiones propias se tomaron.

*(sin entradas todavía)*

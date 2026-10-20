# Historial de cambios

Entradas de la más reciente a la más antigua. Cada sesión de trabajo con cambios añade una.

## 2026-10-20: Pestaña «Seguros»

- La pestaña «Seguros de vida» pasa a llamarse **Seguros** en web y escritorio (petición de
  Antonio). Solo cambia el rótulo: sin cambios de cálculo, la nota técnica no se toca.
- HTML autocontenido, `index.html` y `.exe` recompilados.

## 2026-10-20: Cierre de la fase 2

- La fase 2 (seguros sobre una cabeza) queda cerrada con lo hecho el 2026-10-07.
- La función de densidad de la vida residual sale de la fase 2 y pasa a la lista de espera
  (`CLAUDE.md` §7.4), porque Antonio aún no la ha estudiado. Sin cambios de cálculo ni de
  interfaz: no se toca la nota técnica ni se recompila.

## 2026-10-07: Fase 2 · Seguros de vida, interés técnico y recargo de seguridad

- Nueva pestaña **Seguros de vida** (web y escritorio): temporal a n años, vida entera,
  capital diferido y mixto, diferidos m años (salvo el capital diferido), con pago al final
  del año de fallecimiento. El mixto admite capital de fallecimiento C_f y de supervivencia C_s
  distintos y muestra por separado sus dos partes. Distribución del valor actual Z (valores
  iguales agrupados, ordenada por valor), momentos de orden s, prima pura única, métricas de
  riesgo (VaR y TVaR 99,5 %) y funciones de masa y distribución. Base técnica verificada por
  Antonio antes de programar (apuntes 8–9 de Seguros de Vida).
- **Rentas y seguros:** interés por defecto 1,95 %, tipo técnico DGSFP 2026
  (BOE-A-2026-1226), editable y con botón para volver a él; **recargo de seguridad α** libre
  con prima pura, importe del recargo y prima recargada (1 + α)·E.
- Motor reorganizado en capas: `descuento.py`/`.js` (v(t), tipo técnico), `distribucion.py`/`.js`
  (agregación, momentos, métricas, prima) y los productos `rentas` y `seguros`.
  En la web, piezas comunes de las dos pestañas en `comun.jsx`; en escritorio, clase `DistTab`.
- **Corrección destapada por la paridad:** varianza, asimetría y curtosis se calculan con
  momentos centrales directos. Con la fórmula a partir de los ordinarios, distribuciones casi
  degeneradas (vida entera con I = 0) daban asimetrías de ~10⁸ distintas en Python y en JS.
  Afecta a rentas en el último decimal; la diferencia Python/JS baja de ~10⁻¹¹ a ≤ 5·10⁻¹⁴.
- Tests: `test_seguros.py` y `seguros.test.mjs` (Σ prob = 1, conmutación, Aₓ = 1 − d·äₓ,
  descomposiciones, ²A, recargo, validación) y seguros en la prueba de paridad.
  383 tests en Python y 181 en JS.
- `docs/NOTA_TECNICA.md` v1.2 (§9 Seguros de vida, §10 Descuento, interés técnico y prima
  recargada; secciones 9–11 renumeradas como 11–13). `CLAUDE.md`: §2.2, §2.3, estado, fase 2
  en curso con sus decisiones, §8 y nuevo paso obligatorio en §6.1: **verificación de la base
  técnica por Antonio antes de programar**. README y `docs/SKILL.md` actualizados.
- Pendiente de la fase 2: función de densidad de la vida residual (aplazada).
- HTML autocontenido e `index.html` recompilados.

## 2026-10-07: Fase 1 · Base de calidad (tests automáticos)

- Nueva carpeta `tests/` con la batería automática y un script único,
  `python tests/ejecutar_tests.py` (también `npm test` en `web/`):
  - `tests/python` (pytest): construcción de lₓ, identidad de control, interpolación y μ,
    e̊ₓ frente a integración numérica y e̊ₓ = eₓ + ½ con UDD, coherencia μ = H′ de los
    modelos, distribución de las rentas (Σ prob = 1, media = valoración pago a pago,
    métricas), validaciones y cotejo con el BOE.
  - `tests/js` (`node --test`): las mismas identidades sobre el motor web.
  - Paridad Python/JS (`test_paridad.py` + `tests/js/volcado.mjs`): datos, presets, q y l,
    ~15 000 casos de tablas, modelos, rentas y mensajes de validación, con tolerancia 10⁻⁸.
- `verificacion_boe.py` se reorganiza en `comprobaciones()` para usarlo desde los tests
  (misma salida al ejecutarlo a mano; devuelve código 1 si algo no cuadra).
- **Correcciones que destaparon los tests:**
  - **PER2020 Individual de 1er orden**: se toma tal cual del anexo 2.1. Antes se derivaba con
    unos recargos reconstruidos en 86–96 que desviaban qₓ hasta 0,007 ‰, λₓ hasta 10⁻⁴ y
    ₙpₓ hasta 8,6·10⁻⁴. Cambia los resultados de esa tabla.
  - Tolerancias del cotejo con el BOE alineadas con lo documentado (0,001 ‰ en q, 10⁻⁴ en λ):
    la PER Colectiva de 1er orden marcaba «DIF» por redondeo del BOE.
  - Rentas con lₓ = 0 (p. ej. PASEM a partir de 111 años): ahora dan un error en las dos
    interfaces; antes, división por cero en escritorio y NaN en la web.
  - Web: eₓ = NaN cuando lₓ = 0, como en Python.
  - Web: `erfc` de precisión doble para Φ en Thiele (antes, aproximación con error ~10⁻⁷ y
    un salto en x = c). Diferencia con Python ahora ~10⁻¹⁵.
  - Web: `validar` comprueba también que m sea entero positivo, como en Python.
- `docs/NOTA_TECNICA.md` v1.1. `CLAUDE.md`: decisiones de la fase 1 y fase activa 2.
- `pytest` añadido a `python/requirements.txt`; `"type": "module"` en `web/package.json`.
- HTML autocontenido e `index.html` recompilados.

## 2026-10-07: Reorganización como proyecto profesional

- La calculadora pasa a ser un proyecto independiente de las asignaturas, orientado a uso
  profesional.
- `CLAUDE.md` se mueve de `docs/` a la raíz y se reescribe: principios, convenciones de
  cálculo, fuentes, arquitectura, estado actual y hoja de ruta (sin el enfoque de asignatura).
- Se añade este `CHANGELOG.md`.
- `README.md`: presentación como herramienta profesional y estructura actualizada.
- `docs/SKILL.md`: sección inicial con la ubicación del proyecto, qué leer al empezar y
  reglas de trabajo; sin referencias a la asignatura.
- Hoja de ruta acordada en `CLAUDE.md` §7: arquitectura en cuatro capas (mortalidad,
  estado, producto, descuento) y fases tests → seguros sobre una cabeza → probabilidades de
  grupo → carteras y exportación; tipo técnico DGSFP 2026 (1,95 %) y recargo de seguridad
  libre en la fase 2; lista de espera con lo aún no estudiado (primas periódicas, reservas,
  curva EIOPA).
- Nueva `docs/NOTA_TECNICA.md` (v1.0): base técnica de todos los cálculos implementados.
- Flujo de trabajo para cada cambio en `CLAUDE.md` §6.1: la nota técnica se actualiza en el
  mismo commit que cualquier cambio de cálculo.

## 2026-10-07: Rentas actuariales y web actualizada

- Pestaña **Rentas actuariales** (Python y web): temporal o vitalicia, pre o postpagable,
  fraccionada, diferida; distribución, momentos y métricas de riesgo (VaR, TVaR 99,5 %).
- HTML autocontenido recompilado.

## Versión inicial (publicada en GitHub)

- Tablas PER2020 y PASEM2020 (2º y 1er orden), diez modelos paramétricos, comparación de
  escenarios y atlas, en web (React) y escritorio (PySide6, `.exe`).
- Verificación de datos contra los anexos del BOE (`verificacion_boe.py`).
- Licencia MIT y publicación en GitHub Pages.

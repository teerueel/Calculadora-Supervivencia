# Historial de cambios

Entradas de la más reciente a la más antigua. Cada sesión de trabajo con cambios añade una.

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

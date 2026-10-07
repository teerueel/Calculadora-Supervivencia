# Historial de cambios

Entradas de la más reciente a la más antigua. Cada sesión de trabajo con cambios añade una.

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

# Calculadora de supervivencia

Calculadora actuarial de probabilidades de supervivencia y fallecimiento con las tablas
españolas PER2020 y PASEM2020 (Resolución de la DGSFP de 17 de diciembre de 2020,
[BOE-A-2020-17154](https://www.boe.es/buscar/doc.php?id=BOE-A-2020-17154)) y con diez leyes
paramétricas de mortalidad.

Herramienta actuarial de uso profesional, nacida en la asignatura **Modelos de
Supervivencia** del Máster en Ciencias Actuariales y Financieras. Dos implementaciones
equivalentes: una aplicación web y una de escritorio.

## Qué calcula

| Magnitud | Significado |
| --- | --- |
| ₙpₓ | probabilidad de que (x) sobreviva n años |
| ₙqₓ | probabilidad de que (x) fallezca dentro de los próximos n años |
| ₘ\|ₙqₓ | probabilidad de que (x) fallezca entre las edades x+m y x+m+n |
| eₓ, e̊ₓ | esperanza de vida abreviada y completa |
| ₖ\|ä⁽ᵐ⁾ₓ:ₙ⌉, ₖ\|a⁽ᵐ⁾ₓ:ₙ⌉ | distribución, momentos de orden s y métricas de una renta actuarial |

La edad x, el plazo n y el diferimiento m admiten decimales. Las edades no enteras se
resuelven repartiendo dentro del año la qₓ publicada, con interpolación lineal (UDD) o
exponencial (fuerza de mortalidad constante), seleccionable.

## Las cinco pestañas

1. **Tablas de mortalidad** — nueve tablas: PER2020 Individual y Colectiva (generacionales,
   con factor de mejora sobre la cohorte) y PASEM2020 General, Rel, NoRel y Decesos
   (estáticas), en segundo y primer orden.
2. **Modelos paramétricos** — exponencial, De Moivre, Gompertz, Makeham, Weibull, Perks,
   Kannisto, Thiele, Siler y Heligman–Pollard, con deslizadores para cada parámetro y la
   tabla de referencia superpuesta.
3. **Comparación** — hasta ocho escenarios mixtos, cada uno con su sexo y, si es un modelo,
   con sus propios parámetros.
4. **Rentas actuariales** — renta temporal o vitalicia, prepagable o postpagable, con m pagos al
   año, cuantía por plazo c (cuantía anual C = m·c), diferimiento k e interés efectivo anual I.
   Muestra la distribución (valores y probabilidades), los momentos E[Yˢ] de los órdenes
   elegidos y, a partir de ellos, media (prima pura única), varianza, desviación típica,
   coeficiente de variación, asimetría, curtosis, cuantiles, VaR y TVaR al 99,5 %.
5. **Atlas** — guía de los modelos paramétricos y de las tablas e hipótesis de interpolación.

En las tres primeras, tres gráficas: supervivencia ₜpₓ, distribución ₜqₓ y tanto instantáneo μₓ₊ₜ.

## Principio de cálculo

Toda probabilidad se obtiene de la función de supervivencia, construida una sola vez:

```
l₀ = 100.000        l_{y+1} = l_y · (1 − q_y)        ω = 121

ₙpₓ = l_{x+n} / l_x        ₙqₓ = 1 − ₙpₓ        ₘ|ₙqₓ = (l_{x+m} − l_{x+m+n}) / l_x
```

Nada de productorios ni de sumatorios acumulados. Los modelos continuos encajan en el mismo
esquema con lₓ = 100.000 · S(x), donde S(x) = e^(−∫μ).

Identidad de control, que las dos implementaciones verifican: ₘqₓ + ₘ|ₙqₓ + ₘ₊ₙpₓ = 1.

### Rentas actuariales

Con v = (1+I)⁻¹, N = m·n plazos y n = w + 1 − x − k en la vitalicia (w = 120):

| Prepagable ₖ\|ä⁽ᵐ⁾ₓ:ₙ⌉ | Postpagable ₖ\|a⁽ᵐ⁾ₓ:ₙ⌉ |
| --- | --- |
| 0 con prob. ₖqₓ (si k > 0) | 0 con prob. ₖ₊₁/ₘqₓ |
| ₖ\|ä⁽ᵐ⁾_{j/m⌉} con prob. ₖ₊₍ⱼ₋₁₎/ₘ\|₁/ₘqₓ, j = 1…N | ₖ\|a⁽ᵐ⁾_{j/m⌉} con prob. ₖ₊ⱼ/ₘ\|₁/ₘqₓ, j = 1…N−1 |
| al último valor se le suma ₖ₊ₙpₓ (temporal) | ₖ\|a⁽ᵐ⁾ₙ⌉ con prob. ₖ₊ₙpₓ (temporal) |

Los momentos son E[Yˢ] = Σ valorˢ · prob. Las probabilidades se leen de lₓ; las edades x + j/m
no enteras usan interpolación lineal (UDD). x es entera; n y k, múltiplos de 1/m.

## Estructura

```
python/   aplicación de escritorio (PySide6 + matplotlib) y generación del .exe
web/      aplicación web (React + recharts) y el HTML autocontenido ya compilado
docs/     NOTA_TECNICA.md (base técnica de los cálculos) y SKILL.md
tests/    tests automáticos (pytest y node --test) y prueba de paridad entre motores
CLAUDE.md convenciones técnicas, decisiones y hoja de ruta
CHANGELOG.md  historial de cambios
```

El motor está separado de la interfaz: `python/datos.py`, `python/tablas.py`,
`python/modelos.py` y `python/rentas.py`, con sus equivalentes en `web/src/data.js`, `web/src/engine.js` y `web/src/rentas.js`. Ambos
motores dan el mismo resultado: los tests lo comprueban con tolerancia 10⁻⁸ y la diferencia
medida es del orden de 10⁻¹⁵ (10⁻¹¹ en los momentos de orden alto de las rentas).

## Ejecutar

Escritorio:

```bash
cd python
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Para el ejecutable de Windows: `build_exe.bat`, que deja `dist\CalculadoraSupervivencia.exe`.

Web: abrir `web/calculadora_supervivencia.html` en el navegador. Para recompilar desde el
código fuente, `npm install && bash build.mjs` dentro de `web/`.

## Tests y verificación de los datos

Una sola orden ejecuta todos los tests (requiere `pytest` y Node.js ≥ 20):

```bash
python tests/ejecutar_tests.py
```

Comprueban la construcción de lₓ, la identidad ₘqₓ + ₘ|ₙqₓ + ₘ₊ₙpₓ = 1, la interpolación y
μ, las esperanzas de vida frente a integración numérica, la coherencia μ = H′ de los modelos,
que la distribución de cada renta suma 1 y que su media coincide con la valoración pago a
pago, la igualdad numérica de los dos motores y los datos frente al BOE. El detalle está en
`docs/NOTA_TECNICA.md` §9.

El cotejo con el BOE también puede lanzarse solo: `python/verificacion_boe.py` compara
casilla por casilla los datos del código con los anexos, extraídos a `boe_anexos.json`:

```bash
cd python && python verificacion_boe.py
```

Los anexos 1.1, 1.2, 1.3, los recargos técnicos del 2.1 y la PER2020 Individual de primer
orden coinciden exactamente. Las tablas de primer orden que el código deriva (PER2020
Colectiva y PASEM2020) difieren como mucho 0,001 ‰ de las publicadas, por el redondeo con
que el BOE las publica (su propio apartado séptimo lo advierte y anuncia un documento con
el desglose completo de decimales).

## Advertencias

- Los **valores iniciales de los parámetros** de los modelos no son valores publicados: son
  un ajuste propio por mínimos cuadrados a la PASEM2020 General de segundo orden de cada
  sexo, reproducible con `python/ajuste_presets.py`. De Moivre se fija en ω = 121 porque su
  ajuste diverge.
- ₙpₓ y ₙqₓ suman 1, pero ₘ|ₙqₓ **no** forma parte de esa partición: se solapa con ambos.
- Las PASEM2020 son estáticas: no se les aplica factor de mejora ni se comparan generaciones
  con ellas.
- Los recargos del anexo 2.1 están tabulados solo para la PER2020 Colectiva. La Individual
  de primer orden se toma por eso tal cual de la tabla publicada en el mismo anexo: aplicarle
  los recargos de la Colectiva desviaría ₙpₓ hasta 6·10⁻⁴ en torno a los 70 años.

## Fuente

Resolución de la Dirección General de Seguros y Fondos de Pensiones de 17 de diciembre
de 2020, BOE núm. 338, de 28 de diciembre de 2020, anexos 1.1 a 2.4.

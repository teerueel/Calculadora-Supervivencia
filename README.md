# Calculadora de supervivencia

Calculadora actuarial de probabilidades de supervivencia y fallecimiento con las tablas
españolas PER2020 y PASEM2020 (Resolución de la DGSFP de 17 de diciembre de 2020,
[BOE-A-2020-17154](https://www.boe.es/buscar/doc.php?id=BOE-A-2020-17154)) y con diez leyes
paramétricas de mortalidad.

Trabajo de la asignatura **Modelos de Supervivencia** del Máster en Ciencias Actuariales y
Financieras. Dos implementaciones equivalentes: una aplicación web y una de escritorio.

## Qué calcula

| Magnitud | Significado |
| --- | --- |
| ₙpₓ | probabilidad de que (x) sobreviva n años |
| ₙqₓ | probabilidad de que (x) fallezca dentro de los próximos n años |
| ₘ\|ₙqₓ | probabilidad de que (x) fallezca entre las edades x+m y x+m+n |
| eₓ, e̊ₓ | esperanza de vida abreviada y completa |

La edad x, el plazo n y el diferimiento m admiten decimales. Las edades no enteras se
resuelven repartiendo dentro del año la qₓ publicada, con interpolación lineal (UDD) o
exponencial (fuerza de mortalidad constante), seleccionable.

## Las cuatro pestañas

1. **Tablas de mortalidad** — nueve tablas: PER2020 Individual y Colectiva (generacionales,
   con factor de mejora sobre la cohorte) y PASEM2020 General, Rel, NoRel y Decesos
   (estáticas), en segundo y primer orden.
2. **Modelos paramétricos** — exponencial, De Moivre, Gompertz, Makeham, Weibull, Perks,
   Kannisto, Thiele, Siler y Heligman–Pollard, con deslizadores para cada parámetro y la
   tabla de referencia superpuesta.
3. **Comparación** — hasta ocho escenarios mixtos, cada uno con su sexo y, si es un modelo,
   con sus propios parámetros.
4. **Atlas** — guía de los modelos paramétricos y de las tablas e hipótesis de interpolación.

En todas, tres gráficas: supervivencia ₜpₓ, distribución ₜqₓ y tanto instantáneo μₓ₊ₜ.

## Principio de cálculo

Toda probabilidad se obtiene de la función de supervivencia, construida una sola vez:

```
l₀ = 100.000        l_{y+1} = l_y · (1 − q_y)        ω = 121

ₙpₓ = l_{x+n} / l_x        ₙqₓ = 1 − ₙpₓ        ₘ|ₙqₓ = (l_{x+m} − l_{x+m+n}) / l_x
```

Nada de productorios ni de sumatorios acumulados. Los modelos continuos encajan en el mismo
esquema con lₓ = 100.000 · S(x), donde S(x) = e^(−∫μ).

Identidad de control, que las dos implementaciones verifican: ₘqₓ + ₘ|ₙqₓ + ₘ₊ₙpₓ = 1.

## Estructura

```
python/   aplicación de escritorio (PySide6 + matplotlib) y generación del .exe
web/      aplicación web (React + recharts) y el HTML autocontenido ya compilado
docs/     CLAUDE.md (convenciones del proyecto) y SKILL.md (procedimiento de cálculo)
```

El motor está separado de la interfaz: `python/datos.py`, `python/tablas.py` y
`python/modelos.py`, con sus equivalentes en `web/src/data.js` y `web/src/engine.js`. Ambos
motores dan el mismo resultado; la diferencia máxima medida es de 1,1·10⁻¹⁶.

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
código fuente, `npm install && bash build.sh` dentro de `web/`.

## Verificación de los datos

`python/verificacion_boe.py` compara casilla por casilla los datos del código con los anexos
del BOE, extraídos a `boe_anexos.json`:

```bash
cd python && python verificacion_boe.py
```

Los anexos 1.1, 1.2, 1.3 y los recargos técnicos del 2.1 coinciden exactamente. Las tablas
de primer orden que el código deriva difieren como mucho 0,001 ‰ de las publicadas, por el
redondeo a tres o cuatro decimales con que el BOE las publica (su propio apartado séptimo lo
advierte y anuncia un documento con el desglose completo de decimales).

## Advertencias

- Los **valores iniciales de los parámetros** de los modelos no son valores publicados: son
  un ajuste propio por mínimos cuadrados a la PASEM2020 General de segundo orden de cada
  sexo, reproducible con `python/ajuste_presets.py`. De Moivre se fija en ω = 121 porque su
  ajuste diverge.
- ₙpₓ y ₙqₓ suman 1, pero ₘ|ₙqₓ **no** forma parte de esa partición: se solapa con ambos.
- Las PASEM2020 son estáticas: no se les aplica factor de mejora ni se comparan generaciones
  con ellas.
- Los recargos del anexo 2.1 están tabulados para la PER2020 Colectiva. La Individual tiene
  los suyos: el mismo desfase de un año que las qₓ, más valores propios entre 86 y 96 años.
  Usar los de la Colectiva desvía ₙpₓ hasta 6·10⁻⁴ en torno a los 70 años.

## Fuente

Resolución de la Dirección General de Seguros y Fondos de Pensiones de 17 de diciembre
de 2020, BOE núm. 338, de 28 de diciembre de 2020, anexos 1.1 a 2.4.

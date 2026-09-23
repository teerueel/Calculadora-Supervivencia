# Calculadora de supervivencia — versión de escritorio (Python)

Aplicación PySide6 + matplotlib equivalente al artifact web. Cuatro pestañas:

1. **Tablas de mortalidad** — PER2020 (Individual y Colectiva) y PASEM2020 (General y
   Decesos), en 2º y 1er orden, agrupadas por tipo (generacional / estática) y uso
   (supervivencia / riesgo / decesos). Calcula ₙpₓ, ₙqₓ, ₘ|ₙqₓ, eₓ y e̊ₓ con x, n y m
   reales (n admite decimales: ₂,₅p₄₅), con interpolación lineal o exponencial.
2. **Modelos paramétricos** — exponencial, De Moivre, Gompertz, Makeham, Weibull, Perks,
   Kannisto, Thiele, Siler y Heligman–Pollard, con deslizadores para cada parámetro.
3. **Comparación** — hasta 8 escenarios (tablas o modelos, con sexo propio). Los
   parámetros de cada modelo se ajustan en la propia pestaña, desplegando el escenario.
4. **Atlas** — guía de los modelos paramétricos y de las tablas e interpolaciones.

En todas: gráficas de ₜpₓ, ₜqₓ y μₓ₊ₜ (escala logarítmica o lineal).

## Ficheros

| Fichero | Contenido |
|---|---|
| `app.py` | Interfaz (punto de entrada) |
| `datos.py` | Tablas del BOE-A-2020-17154 y catálogo de las 9 tablas |
| `tablas.py` | Motor de tablas: vector q, construcción de lₓ, interpolación |
| `modelos.py` | Los 10 modelos paramétricos (μ, S, lₓ = 100.000·S) |
| `presets_data.py` | Valores iniciales de los parámetros (generado) |
| `ajuste_presets.py` | Regenera `presets_data.py` ajustando cada modelo a PASEM2020 General 2º orden |
| `atlas.py` | Contenido de la pestaña Atlas |
| `calculadora.spec`, `build_exe.bat` | Generación del .exe |

## Ejecutar en VSCode

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

En VSCode: *Python: Select Interpreter* → `.venv`, abrir `app.py` y pulsar ▶.

## Generar el .exe (Windows)

Con el entorno activado, doble clic en `build_exe.bat` (o `python -m PyInstaller calculadora.spec`).
Resultado: `dist\CalculadoraSupervivencia.exe`, un único fichero sin consola (~100 MB,
porque incluye Qt y matplotlib). El primer arranque tarda unos segundos mientras se
descomprime.

## Notas

- Los **parámetros iniciales** de los modelos no son valores publicados: son un ajuste
  propio por mínimos cuadrados a la PASEM2020 General 2º orden de cada sexo. De Moivre no
  se ajusta (el ajuste lleva ω por encima de 160) y se fija ω = 121.
- Los valores del BOE están redondeados; puede haber diferencias en el último decimal.

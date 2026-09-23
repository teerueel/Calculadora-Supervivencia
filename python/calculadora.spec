# -*- mode: python ; coding: utf-8 -*-
# PyInstaller: pyinstaller calculadora.spec   →   dist/CalculadoraSupervivencia.exe
a = Analysis(
    ["app.py"],
    pathex=["."],
    hiddenimports=["matplotlib.backends.backend_qtagg"],
    # scipy/numpy solo se usan en ajuste_presets.py: se excluyen para aligerar el .exe
    excludes=["scipy", "tkinter", "PyQt5", "PyQt6", "IPython", "pandas"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="CalculadoraSupervivencia",
    console=False,          # aplicación de ventana, sin consola
    upx=False,
    icon=None,
)

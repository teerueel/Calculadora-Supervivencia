"""Ejecuta todos los tests de la calculadora y resume el resultado.

Uso (desde cualquier carpeta):   python tests/ejecutar_tests.py
Requisitos: Python con pytest (python/requirements.txt) y Node.js ≥ 20 en el PATH.

  1. pytest  tests/python   motor Python: identidades, rentas, modelos, datos frente al BOE
                            y paridad Python/JS (llama al motor web con Node)
  2. node --test tests/js   motor web: las mismas identidades

Devuelve código 0 si todo pasa y 1 si algo falla.
"""
import os
import shutil
import subprocess
import sys
import time

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def paso(nombre, cmd, cwd):
    print(f"\n=== {nombre} ===", flush=True)
    t = time.time()
    r = subprocess.run(cmd, cwd=cwd)
    seg = time.time() - t
    return nombre, r.returncode == 0, seg


def main():
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    res = []
    res.append(paso("Python (pytest)", [sys.executable, "-m", "pytest", "tests/python", "-q", "-p", "no:cacheprovider"], RAIZ))
    node = shutil.which("node")
    if node:
        res.append(paso("Web (node --test)", [node, "--test", "tests/js/*.test.mjs"], RAIZ))
    else:
        print("\nNo se encuentra Node.js en el PATH: no se pueden ejecutar los tests del motor web.")
        res.append(("Web (node --test)", False, 0.0))
    print("\n=== Resumen ===")
    for nombre, ok, seg in res:
        print(f"  {'OK   ' if ok else 'FALLO'}  {nombre}  ({seg:.0f} s)")
    todo = all(ok for _, ok, _ in res)
    print("\nTodo correcto." if todo else "\nHay fallos: revisa la salida de arriba.")
    return 0 if todo else 1


if __name__ == "__main__":
    sys.exit(main())

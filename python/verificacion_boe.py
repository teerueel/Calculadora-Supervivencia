"""Compara los datos del código con los anexos del BOE-A-2020-17154.

Uso: python verificacion_boe.py   (necesita boe_anexos.json en la misma carpeta)

`comprobaciones()` devuelve la lista de cotejos (grupo, nombre, discrepancias); la usan
también los tests automáticos (tests/python/test_boe.py).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datos


def cargar_boe():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "boe_anexos.json")
    with open(ruta, encoding="utf-8") as f:
        B = json.load(f)
    return {k: {int(a): v for a, v in d.items()} for k, d in B.items()}


def cmpar(mio, boe, tol=0.0):
    """Edades 0..120 en las que el código y el BOE difieren más de la tolerancia."""
    return [(a, mio[a], boe[a]) for a in range(121) if abs(mio[a] - boe[a]) > tol + 1e-9]


def comprobaciones():
    B = cargar_boe()
    A11, A12, A21C, A21I, A22 = B["A11"], B["A12"], B["A21C"], B["A21I"], B["A22"]
    col = lambda A, i: {a: A[a][i] for a in A}  # noqa: E731
    out = []

    def add(grupo, nombre, mio, boe, tol=0.0):
        out.append((grupo, nombre, cmpar(mio, boe, tol)))

    g = "Anexo 1.1 · PER2020 2º orden (datos del código)"
    add(g, "PER Col q mujeres", datos.PER_COL_Q_M, col(A11, 0))
    add(g, "PER Col λ mujeres", datos.PER_COL_L_M, col(A11, 1))
    add(g, "PER Col q hombres", datos.PER_COL_Q_H, col(A11, 2))
    add(g, "PER Col λ hombres", datos.PER_COL_L_H, col(A11, 3))
    ind = datos.TABLES["per_ind_2"]["data"]
    add(g, "PER Ind q mujeres (derivada)", ind["M"]["qb"], col(A11, 4))
    add(g, "PER Ind λ mujeres (derivada)", ind["M"]["lam"], col(A11, 5))
    add(g, "PER Ind q hombres (derivada)", ind["H"]["qb"], col(A11, 6))
    add(g, "PER Ind λ hombres (derivada)", ind["H"]["lam"], col(A11, 7))

    g = "Anexos 1.2 y 1.3 · PASEM2020 2º orden"
    add(g, "PASEM General mujeres", datos.PASEM_GEN_M, col(A12, 0))
    add(g, "PASEM General hombres", datos.PASEM_GEN_H, col(A12, 1))
    add(g, "PASEM Decesos mujeres", datos.PASEM_DEC_M, col(A12, 2))
    add(g, "PASEM Decesos hombres", datos.PASEM_DEC_H, col(A12, 3))

    g = "Anexo 2.1 · recargos técnicos"
    add(g, "Recargo q mujeres (Col)", datos.REC_Q_M, col(A21C, 0))
    add(g, "Recargo q hombres (Col)", datos.REC_Q_H, col(A21C, 4))
    add(g, "Recargo λ mujeres (Col)", datos.REC_L, col(A21C, 2))
    add(g, "Recargo λ hombres (Col)", datos.REC_L, col(A21C, 6))

    # PER Individual de 1er orden: se toma tal cual del anexo 2.1 (coincidencia exacta).
    g = "Anexo 2.1 · PER2020 Individual 1er orden (datos del código)"
    d = datos.TABLES["per_ind_1"]["data"]
    add(g, "per_ind_1 q mujeres", d["M"]["qb"], col(A21I, 1))
    add(g, "per_ind_1 λ mujeres", d["M"]["lam"], col(A21I, 3))
    add(g, "per_ind_1 q hombres", d["H"]["qb"], col(A21I, 5))
    add(g, "per_ind_1 λ hombres", d["H"]["lam"], col(A21I, 7))

    # El resto de 1er orden se construye en el código; el BOE las publica redondeadas
    # (apartado séptimo): tolerancia de 0,001 ‰ en q y una unidad del 4º decimal en λ.
    TQ, TL = 0.001, 0.0001
    g = "Tablas de 1er orden que construye el código, frente al BOE"
    d = datos.TABLES["per_col_1"]["data"]
    add(g, "per_col_1 q mujeres", d["M"]["qb"], col(A21C, 1), TQ)
    add(g, "per_col_1 λ mujeres", d["M"]["lam"], col(A21C, 3), TL)
    add(g, "per_col_1 q hombres", d["H"]["qb"], col(A21C, 5), TQ)
    add(g, "per_col_1 λ hombres", d["H"]["lam"], col(A21C, 7), TL)
    for key, c in (("pasem_rel_1", 0), ("pasem_norel_1", 2), ("pasem_dec_1", 4)):
        d = datos.TABLES[key]["data"]
        add(g, key + " mujeres", d["M"], col(A22, c), TQ)
        add(g, key + " hombres", d["H"], col(A22, c + 1), TQ)
    return out


def main():
    grupo, fallos = None, 0
    for g, nombre, bad in comprobaciones():
        if g != grupo:
            print(f"== {g} ==")
            grupo = g
        print(f"{nombre:42s} {'OK' if not bad else str(len(bad)) + ' DIF'}", end="")
        print("" if not bad else "  " + str(bad[:6]))
        fallos += bool(bad)
    return fallos


if __name__ == "__main__":
    sys.exit(1 if main() else 0)

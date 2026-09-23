"""Compara los datos del código con los anexos del BOE-A-2020-17154.

Uso: python verificacion_boe.py   (necesita boe_anexos.json en la misma carpeta)
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datos, tablas
B = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "boe_anexos.json"))); B = {k: {int(a): v for a, v in d.items()} for k, d in B.items()}
A11, A12, A21C, A21I, A22 = B["A11"], B["A12"], B["A21C"], B["A21I"], B["A22"]

def cmpar(nombre, mio, boe, tol=0.0):
    bad = [(a, mio[a], boe[a]) for a in range(121) if abs(mio[a] - boe[a]) > tol + 1e-9]
    print(f"{nombre:42s} {'OK' if not bad else str(len(bad)) + ' DIF'}", end="")
    print("" if not bad else "  " + str(bad[:6]))
    return bad

print("== Anexo 1.1 · PER2020 2º orden (datos del código) ==")
cmpar("PER Col q mujeres", datos.PER_COL_Q_M, {a: A11[a][0] for a in A11})
cmpar("PER Col λ mujeres", datos.PER_COL_L_M, {a: A11[a][1] for a in A11})
cmpar("PER Col q hombres", datos.PER_COL_Q_H, {a: A11[a][2] for a in A11})
cmpar("PER Col λ hombres", datos.PER_COL_L_H, {a: A11[a][3] for a in A11})
ind = datos.TABLES["per_ind_2"]["data"]
cmpar("PER Ind q mujeres (derivada)", ind["M"]["qb"], {a: A11[a][4] for a in A11})
cmpar("PER Ind λ mujeres (derivada)", ind["M"]["lam"], {a: A11[a][5] for a in A11})
cmpar("PER Ind q hombres (derivada)", ind["H"]["qb"], {a: A11[a][6] for a in A11})
cmpar("PER Ind λ hombres (derivada)", ind["H"]["lam"], {a: A11[a][7] for a in A11})

print("== Anexos 1.2 y 1.3 · PASEM2020 2º orden ==")
cmpar("PASEM General mujeres", datos.PASEM_GEN_M, {a: A12[a][0] for a in A12})
cmpar("PASEM General hombres", datos.PASEM_GEN_H, {a: A12[a][1] for a in A12})
cmpar("PASEM Decesos mujeres", datos.PASEM_DEC_M, {a: A12[a][2] for a in A12})
cmpar("PASEM Decesos hombres", datos.PASEM_DEC_H, {a: A12[a][3] for a in A12})

print("== Anexo 2.1 · recargos técnicos ==")
cmpar("Recargo q mujeres (Col)", datos.REC_Q_M, {a: A21C[a][0] for a in A21C})
cmpar("Recargo q hombres (Col)", datos.REC_Q_H, {a: A21C[a][4] for a in A21C})
cmpar("Recargo λ mujeres (Col)", datos.REC_L, {a: A21C[a][2] for a in A21C})
cmpar("Recargo λ hombres (Col)", datos.REC_L, {a: A21C[a][6] for a in A21C})

print("== Tablas de 1er orden que construye el código, frente al BOE ==")
for key, boe, cols in (("per_col_1", A21C, (1, 3, 5, 7)), ("per_ind_1", A21I, (1, 3, 5, 7))):
    d = datos.TABLES[key]["data"]
    cmpar(key + " q mujeres", d["M"]["qb"], {a: boe[a][cols[0]] for a in boe}, 0.0005)
    cmpar(key + " λ mujeres", d["M"]["lam"], {a: boe[a][cols[1]] for a in boe}, 0.00005)
    cmpar(key + " q hombres", d["H"]["qb"], {a: boe[a][cols[2]] for a in boe}, 0.0005)
    cmpar(key + " λ hombres", d["H"]["lam"], {a: boe[a][cols[3]] for a in boe}, 0.00005)
for key, col in (("pasem_rel_1", 0), ("pasem_norel_1", 2), ("pasem_dec_1", 4)):
    d = datos.TABLES[key]["data"]
    cmpar(key + " mujeres", d["M"], {a: A22[a][col] for a in A22}, 0.0005)
    cmpar(key + " hombres", d["H"], {a: A22[a][col + 1] for a in A22}, 0.0005)

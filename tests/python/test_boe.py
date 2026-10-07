"""Los datos del código coinciden con los anexos del BOE-A-2020-17154 (verificacion_boe.py)."""
import pytest

import verificacion_boe

COTEJOS = verificacion_boe.comprobaciones()


@pytest.mark.parametrize("grupo,nombre,discrepancias", COTEJOS, ids=[c[1] for c in COTEJOS])
def test_coincide_con_boe(grupo, nombre, discrepancias):
    assert not discrepancias, f"{grupo} · {nombre}: (edad, código, BOE) {discrepancias[:6]}"


def test_se_cotejan_todas_las_tablas():
    # 8 PER 2º orden + 4 PASEM 2º + 4 recargos + 4 PER Ind 1er + 4 PER Col 1er + 6 PASEM 1er
    assert len(COTEJOS) == 30

"""
Capa de descuento (CLAUDE.md §7.1, capa 4): la función v(t) con la que se actualizan los pagos.

Hoy, tipo efectivo anual constante I:   v = (1 + I)^(−1),   v(t) = v^t.
Rentas y seguros solo piden factores v(t) a esta capa; una curva de tipos sustituiría a factor()
sin tocar los productos.

TIPO_TECNICO es el tipo de interés máximo que publica cada enero la DGSFP para el cálculo de la
provisión de seguros de vida (art. 33 del ROSSP). Se ofrece como valor por defecto y es editable.
"""
import math

TIPO_TECNICO = dict(
    año=2026,
    I=0.0195,
    ref="Resolución de la DGSFP de 9 de enero de 2026 (BOE-A-2026-1226, de 19 de enero)",
)


def validar_interes(I):
    if not math.isfinite(I) or I <= -1:
        return "El tipo de interés I debe ser mayor que −100 %."
    return None


def factor(I):
    """v(t) = (1 + I)^(−t), con v = 1/(1 + I) calculado una vez."""
    v = 1.0 / (1.0 + I)
    return lambda t: v ** t  # noqa: E731

/* Capa de descuento — espejo de descuento.py.
   Tipo efectivo anual constante I: v = (1 + I)^−1, v(t) = v^t. Rentas y seguros solo piden
   factores v(t) a esta capa. TIPO_TECNICO: tipo máximo que publica cada enero la DGSFP para la
   provisión de seguros de vida (art. 33 ROSSP); valor por defecto, editable. */
export const TIPO_TECNICO = {
  año: 2026,
  I: 0.0195,
  ref: "Resolución de la DGSFP de 9 de enero de 2026 (BOE-A-2026-1226, de 19 de enero)",
};

export function validarInteres(I) {
  if (!Number.isFinite(I) || I <= -1) return "El tipo de interés I debe ser mayor que −100 %.";
  return null;
}

/* v(t) = (1 + I)^(−t), con v = 1/(1 + I) calculado una vez */
export function factor(I) {
  const v = 1 / (1 + I);
  return (t) => Math.pow(v, t);
}

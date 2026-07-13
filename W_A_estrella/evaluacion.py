from typing import List
from modelos import Paciente

# NOTA: tanto calcular_g como calcular_h delegan el costo de cada paciente en
# Paciente.obtener_riesgo_total (modelos.py), que ahora combina:
#   s_estatico + s_dinamico  (sp/s'p del paper, score clínico)
#   + PESO_VULNERABILIDAD * min(vp(t), VP_TOPE)  (vulnerabilidad, config_modelo.py)
# Por lo tanto f(n) = g(n) + w*h(n) ya considera vp(t) sin necesidad de tocar
# este archivo más allá de este comentario: el cambio vive en modelos.py.

def calcular_g(paciente_nuevo: Paciente, g_anterior: float, pesos_estaticos: dict, pesos_dinamicos: dict, tasas_lambda: dict) -> float:
    #g(n): pacientes ya agendados se evalúan con dias_extra=0.
    riesgo_paciente = paciente_nuevo.obtener_riesgo_total(
        pesos_estaticos, pesos_dinamicos, dias_extra=0, tasas_lambda=tasas_lambda
    )
    return g_anterior + riesgo_paciente


def calcular_h(pacientes_pendientes: List[Paciente], pesos_estaticos: dict, pesos_dinamicos: dict, tasas_lambda: dict, dias_postergacion: int = 7) -> float:
    """h(n): pendientes se evalúan con dias_extra=dias_postergacion (esperan 1 semana más).
    esta heurística asume que todo paciente pendiente esperará exactamente
    dias_postergacion días más, incluso aquellos que en la práctica terminarían
    agendados en la misma semana (con costo real dias_extra=0, menor al asumido
    aquí). Eso sobreestima el costo futuro de esos casos puntuales, por lo que
    h(n) no es estrictamente admisible en sentido estricto (podría sobreestimar
    el costo óptimo restante). En la práctica esto no es un problema para este
    proyecto porque ya se usa w=2.0 en f(n) = g(n) + w*h(n), lo que renuncia a
    la garantía de optimalidad a propósito para acelerar la búsqueda (Weighted
    A*, no A* puro)
    """
    riesgo_estimado = 0.0
    for paciente in pacientes_pendientes:
        riesgo_estimado += paciente.obtener_riesgo_total(
            pesos_estaticos, pesos_dinamicos, dias_extra=dias_postergacion, tasas_lambda=tasas_lambda
        )
    return riesgo_estimado
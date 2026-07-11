from typing import List
from modelos import Paciente

def calcular_g(paciente_nuevo: Paciente, g_anterior: float, pesos_estaticos: dict, pesos_dinamicos: dict, tasas_lambda: dict) -> float:
    #g(n): pacientes ya agendados se evalúan con dias_extra=0.
    riesgo_paciente = paciente_nuevo.obtener_riesgo_total(
        pesos_estaticos, pesos_dinamicos, dias_extra=0, tasas_lambda=tasas_lambda
    )
    return g_anterior + riesgo_paciente


def calcular_h(pacientes_pendientes: List[Paciente], pesos_estaticos: dict, pesos_dinamicos: dict, tasas_lambda: dict, dias_postergacion: int = 7) -> float:
    #h(n): pendientes se evalúan con dias_extra=dias_postergacion (esperan 1 semana más).
    riesgo_estimado = 0.0
    for paciente in pacientes_pendientes:
        riesgo_estimado += paciente.obtener_riesgo_total(
            pesos_estaticos, pesos_dinamicos, dias_extra=dias_postergacion, tasas_lambda=tasas_lambda
        )
    return riesgo_estimado
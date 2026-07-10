from typing import List
from modelos import Paciente

def calcular_g(paciente_nuevo: Paciente, g_anterior: float, tiempo_asignacion: int, 
               pesos_estaticos: dict, pesos_dinamicos: dict, tasas_lambda: dict) -> float:
    #Calcula el riesgo acumulado real g(n) de la agenda construida
    riesgo_paciente = paciente_nuevo.obtener_riesgo_total(
        pesos_estaticos, pesos_dinamicos, tiempo_asignacion, tasas_lambda
    )
    return g_anterior + riesgo_paciente

def calcular_h(pacientes_pendientes: List[Paciente], tiempo_disponible_futuro: int, 
               pesos_estaticos: dict, pesos_dinamicos: dict, tasas_lambda: dict) -> float:
    """Calcula el riesgo futuro estimado h(n)
    Asume asignación en los próximos slots disponibles para mantener admisibilidad."""
    riesgo_estimado = 0.0
    for paciente in pacientes_pendientes:
        riesgo_estimado += paciente.obtener_riesgo_total(
            pesos_estaticos, pesos_dinamicos, tiempo_disponible_futuro, tasas_lambda
        )
    return riesgo_estimado
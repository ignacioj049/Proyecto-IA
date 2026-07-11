from typing import List, Dict
from scoring import alpha_dinamico

class Paciente:
    def __init__(self, id_paciente: int, tiempo_quirurgico: int,
                 vars_estaticas: Dict[str, float], vars_dinamicas: Dict[str, float],
                 tipo_diag: str, dias_espera_base: int):
        self.id = id_paciente
        self.tiempo_quirurgico = tiempo_quirurgico
        self.vars_estaticas = vars_estaticas
        self.vars_dinamicas_base = vars_dinamicas
        self.tipo_diag = tipo_diag
        self.dias_espera_base = dias_espera_base
        self.dias_pospuestos = 0 

    def calcular_score_estatico(self, pesos_estaticos: Dict[str, float]) -> float:
        score = 0.0
        for var, alpha in self.vars_estaticas.items():
            score += pesos_estaticos.get(var, 0) * alpha
        return score

    def calcular_score_dinamico(self, pesos_dinamicos: Dict[str, float],
                                dias_extra: float, tasas_lambda: Dict[str, List[float]]) -> float:
        """s'p(t) proyectando dias_extra días sobre dias_espera_base.
        dias_extra=0 -> paciente evaluado como si se operara esta semana.
        dias_extra=dias_postergacion -> paciente evaluado como si quedara
        pendiente y esperara una semana más"""
        score = 0.0
        t_total_dias = self.dias_espera_base + dias_extra
        lambdas_paciente = tasas_lambda.get(self.tipo_diag, [0, 0, 0, 0])

        for var, alpha_base in self.vars_dinamicas_base.items():
            alpha_din = alpha_dinamico(alpha_base, lambdas_paciente, t_total_dias)
            score += pesos_dinamicos.get(var, 0) * alpha_din
        return score

    def obtener_riesgo_total(self, pesos_estaticos: Dict[str, float], pesos_dinamicos: Dict[str, float],
                             dias_extra: float, tasas_lambda: Dict[str, List[float]]) -> float:
        s_estatico = self.calcular_score_estatico(pesos_estaticos)
        s_dinamico = self.calcular_score_dinamico(pesos_dinamicos, dias_extra, tasas_lambda)
        return s_estatico + s_dinamico


class EstadoNodo:
    # tiempo_simulado_actual se conserva solo para trazabilidad de capacidad
    def __init__(self, agenda_parcial: List[Paciente], pacientes_pendientes: List[Paciente],
                 tiempo_restante: int, g: float, h: float, w: float, tiempo_simulado_actual: int):
        # Asignaciones limpias, sin citas incrustadas
        self.agenda_parcial = agenda_parcial
        self.pacientes_pendientes = pacientes_pendientes
        self.tiempo_restante = tiempo_restante
        self.tiempo_simulado_actual = tiempo_simulado_actual
        
        # Evaluación matemática f(n) = g(n) + w * h(n)
        self.g = g
        self.h = h
        self.w = w
        self.f = self.g + (self.w * self.h)

    def __lt__(self, otro):
        # Permite que la cola de prioridad (heapq) extraiga siempre el nodo con el menor f(n)
        return self.f < otro.f
from typing import List, Dict
from scoring import alpha_dinamico
from config_modelo import PESO_VULNERABILIDAD, VP_TOPE

class Paciente:
    def __init__(self, id_paciente: int, tiempo_quirurgico: int,
                 vars_estaticas: Dict[str, float], vars_dinamicas: Dict[str, float],
                 tipo_diag: str, dias_espera_base: int, jclin_meses: float = None):
        self.id = id_paciente
        self.tiempo_quirurgico = tiempo_quirurgico
        self.vars_estaticas = vars_estaticas
        self.vars_dinamicas_base = vars_dinamicas
        self.tipo_diag = tipo_diag
        self.dias_espera_base = dias_espera_base
        self.dias_pospuestos = 0
        # jclin_meses: tiempo máximo de espera indicado por el médico (meses).
        # Se guarda para poder calcular vp(t) = (t - fp) / Jclin_p (Ecuación 4
        # del paper) directamente sobre el objeto Paciente, igual que hace
        # scoring.vulnerabilidad(...) sobre las filas de un DataFrame.
        self.jclin_meses = jclin_meses

    def vulnerabilidad(self, dias_extra: float = 0) -> float:
        """vp(t) — Ecuación (4) del paper, ver scoring.vulnerabilidad().
        Devuelve None si no se dispone de jclin_meses (paciente sin ese dato)."""
        if not self.jclin_meses:
            return None
        t_total = self.dias_espera_base + dias_extra
        jclin_dias = self.jclin_meses * 30.44
        return t_total / jclin_dias

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
        """Riesgo total usado por wA* para ordenar/costear pacientes (g(n) y h(n)).

        riesgo_total = s_estatico + s_dinamico + PESO_VULNERABILIDAD * min(vp(t), VP_TOPE)

        Antes, esta función solo devolvía s_estatico + s_dinamico (score clínico
        general, sp/s'p del paper), por lo que la búsqueda de wA* era ciega a
        vp(t) = (t - fp)/Jclin_p: un paciente podía llevar años sobrepasando su
        propio plazo clínico máximo sin que eso influyera en su prioridad. Se
        suma aquí un término ponderado y acotado de vp(t) (ver config_modelo.py,
        sección 5) para que la vulnerabilidad SÍ empuje el costo de dejarlo
        pendiente, sin dejar que un caso extremo domine por completo el resto
        del score.
        """
        s_estatico = self.calcular_score_estatico(pesos_estaticos)
        s_dinamico = self.calcular_score_dinamico(pesos_dinamicos, dias_extra, tasas_lambda)
        riesgo_clinico = s_estatico + s_dinamico

        vp = self.vulnerabilidad(dias_extra)
        if vp is None:
            # Paciente sin Jclin_meses disponible: no se puede calcular vp(t),
            # se mantiene el comportamiento anterior (solo riesgo clínico).
            return riesgo_clinico

        vp_acotado = min(vp, VP_TOPE)
        return riesgo_clinico + PESO_VULNERABILIDAD * vp_acotado


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
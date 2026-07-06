from typing import List, Dict

class Paciente:
    #Representación de un paciente con variables clínicas y psicosociales
    
    def __init__(self, id_paciente: int, tiempo_quirurgico: int, 
                 vars_estaticas: Dict[str, float], vars_dinamicas: Dict[str, float],
                 tipo_diag: str, dias_espera_base: int):
        self.id = id_paciente
        self.tiempo_quirurgico = tiempo_quirurgico
        self.vars_estaticas = vars_estaticas 
        self.vars_dinamicas_base = vars_dinamicas
        self.tipo_diag = tipo_diag  # 'A', 'B', o 'C' (viene de tu dataset)
        self.dias_espera_base = dias_espera_base # Días que ya lleva esperando
        
    def calcular_score_estatico(self, pesos_estaticos: Dict[str, float]) -> float:
        score = 0.0
        for var, alpha in self.vars_estaticas.items():
            score += pesos_estaticos.get(var, 0) * alpha
        return score

    def _alpha_dinamico(self, alpha_0: float, t_dias: int, lambdas_tipo: List[float]) -> float:
        
        """Fórmula recursiva exacta de tu dataset para el deterioro temporal α̃(k,h).
        Se ejecuta por intervalos: 90, 180, 360 y 540 días."""
        t = min(t_dias, 540) 
        
        if t <= 90:
            return (1 + (t / 90) * lambdas_tipo[0]) * alpha_0
        
        a90 = (1 + lambdas_tipo[0]) * alpha_0
        if t <= 180:
            return (1 + ((t - 90) / 90) * lambdas_tipo[1]) * a90
        
        a180 = (1 + lambdas_tipo[1]) * a90
        if t <= 360:
            return (1 + ((t - 180) / 180) * lambdas_tipo[2]) * a180
            
        a360 = (1 + lambdas_tipo[2]) * a180
        return (1 + ((t - 360) / 180) * lambdas_tipo[3]) * a360

    def calcular_score_dinamico(self, pesos_dinamicos: Dict[str, float], 
                                dias_proyectados: int, tasas_lambda: Dict[str, List[float]]) -> float:
        #Calcula el deterioro proyectado sumando los días actuales más la proyección del wA*
        score = 0.0
        # El tiempo total evalúa la evolución de la enfermedad
        t_total_dias = self.dias_espera_base + dias_proyectados
        lambdas_paciente = tasas_lambda.get(self.tipo_diag, [0, 0, 0, 0])
        
        for var, alpha_base in self.vars_dinamicas_base.items():
            alpha_din = self._alpha_dinamico(alpha_base, t_total_dias, lambdas_paciente)
            score += pesos_dinamicos.get(var, 0) * alpha_din
            
        return score

    def obtener_riesgo_total(self, pesos_estaticos: Dict[str, float], pesos_dinamicos: Dict[str, float], 
                             dias_proyectados: int, tasas_lambda: Dict[str, List[float]]) -> float:
        #Retorna s'_p(t) completo sumando la parte estática y la dinámica
        s_estatico = self.calcular_score_estatico(pesos_estaticos)
        s_dinamico = self.calcular_score_dinamico(pesos_dinamicos, dias_proyectados, tasas_lambda)
        return s_estatico + s_dinamico


class EstadoNodo:
    #Tupla de estado para el espacio de búsqueda del wA*
    
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
        #Permite que la cola de prioridad (heapq) extraiga siempre el nodo con el menor f(n)
        return self.f < otro.f
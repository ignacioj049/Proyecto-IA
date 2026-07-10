import heapq
from typing import List
from modelos import Paciente, EstadoNodo
from evaluacion import calcular_g, calcular_h

def weighted_a_star(pacientes_totales: List[Paciente], capacidad_quirurgica: int, 
                    w: float, pesos_estaticos: dict, pesos_dinamicos: dict, 
                    tasas_lambda: dict) -> EstadoNodo:
    #Ejecuta el algoritmo wA* para optimizar la agenda globalmente
    
    # 1. Estado inicial con agenda vacía
    nodo_inicial = EstadoNodo(
        agenda_parcial=[],
        pacientes_pendientes=pacientes_totales.copy(),
        tiempo_restante=capacidad_quirurgica,
        tiempo_simulado_actual=0,
        g=0.0,
        h=calcular_h(pacientes_totales, 0, pesos_estaticos, pesos_dinamicos, tasas_lambda),
        w=w
    )
    
    frontera = []
    heapq.heappush(frontera, nodo_inicial)
    iteraciones = 0
    while frontera:
        nodo_actual = heapq.heappop(frontera)
        iteraciones += 1
        if iteraciones % 100 == 0:
            print(f"⏳ Explorando... Nodos evaluados: {iteraciones} | Pacientes en agenda temporal: {len(nodo_actual.agenda_parcial)}")
        
        # Condición de Parada: Agenda completa[cite: 2]
        if not nodo_actual.pacientes_pendientes or nodo_actual.tiempo_restante <= 0:
            return nodo_actual
            
        # Expansión de nodos
        for paciente in nodo_actual.pacientes_pendientes:
            if paciente.tiempo_quirurgico <= nodo_actual.tiempo_restante:
                
                nueva_agenda = nodo_actual.agenda_parcial + [paciente]
                nuevos_pendientes = [p for p in nodo_actual.pacientes_pendientes if p.id != paciente.id]
                nuevo_tiempo_restante = nodo_actual.tiempo_restante - paciente.tiempo_quirurgico
                nuevo_tiempo_simulado = nodo_actual.tiempo_simulado_actual + paciente.tiempo_quirurgico
                
                # Calcular f(n)
                nuevo_g = calcular_g(
                    paciente, nodo_actual.g, nuevo_tiempo_simulado, 
                    pesos_estaticos, pesos_dinamicos, tasas_lambda
                )
                nuevo_h = calcular_h(
                    nuevos_pendientes, nuevo_tiempo_simulado, 
                    pesos_estaticos, pesos_dinamicos, tasas_lambda
                )
                
                nodo_hijo = EstadoNodo(
                    agenda_parcial=nueva_agenda,
                    pacientes_pendientes=nuevos_pendientes,
                    tiempo_restante=nuevo_tiempo_restante,
                    tiempo_simulado_actual=nuevo_tiempo_simulado,
                    g=nuevo_g,
                    h=nuevo_h,
                    w=w
                )
                
                heapq.heappush(frontera, nodo_hijo)
                
    return None
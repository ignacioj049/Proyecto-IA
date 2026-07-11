import heapq
from typing import List
from modelos import Paciente, EstadoNodo
from evaluacion import calcular_g, calcular_h

def weighted_a_star(pacientes_totales: List[Paciente], capacidad_quirurgica: int,
                    w: float, pesos_estaticos: dict, pesos_dinamicos: dict,
                    tasas_lambda: dict, top_k_candidatos: int) -> EstadoNodo:

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
    visitados = {} 
    iteraciones = 0

    while frontera:
        nodo_actual = heapq.heappop(frontera)
        iteraciones += 1

        # Poda por estado repetido 
        firma = frozenset(p.id for p in nodo_actual.agenda_parcial)
        if firma in visitados and visitados[firma] <= nodo_actual.g:
            continue
        visitados[firma] = nodo_actual.g

        if iteraciones % 50 == 0:
            print(f"Nodos evaluados: {iteraciones} | Agenda parcial: {len(nodo_actual.agenda_parcial)} | Frontera: {len(frontera)}")

        # Meta: sin pendientes, o ningún pendiente cabe en el tiempo restante 
        cabe_alguno = any(p.tiempo_quirurgico <= nodo_actual.tiempo_restante
                           for p in nodo_actual.pacientes_pendientes)
        if not nodo_actual.pacientes_pendientes or nodo_actual.tiempo_restante <= 0 or not cabe_alguno:
            print(f"\nSolución encontrada en {iteraciones} iteraciones.")
            return nodo_actual

        top_candidatos = sorted(
            nodo_actual.pacientes_pendientes,
            key=lambda p: p.obtener_riesgo_total(
                pesos_estaticos, pesos_dinamicos, nodo_actual.tiempo_simulado_actual, tasas_lambda
            ),
            reverse=True
        )[:top_k_candidatos]

        for paciente in top_candidatos:
            if paciente.tiempo_quirurgico <= nodo_actual.tiempo_restante:
                nueva_agenda = nodo_actual.agenda_parcial + [paciente]
                nuevos_pendientes = [p for p in nodo_actual.pacientes_pendientes if p.id != paciente.id]
                nuevo_tiempo_restante = nodo_actual.tiempo_restante - paciente.tiempo_quirurgico
                nuevo_tiempo_simulado = nodo_actual.tiempo_simulado_actual + paciente.tiempo_quirurgico

                firma_hija = frozenset(p.id for p in nueva_agenda)
                nuevo_g = calcular_g(paciente, nodo_actual.g, nuevo_tiempo_simulado,
                                      pesos_estaticos, pesos_dinamicos, tasas_lambda)

                # No expandir si ya visitamos ese mismo subconjunto con g igual o mejor
                if firma_hija in visitados and visitados[firma_hija] <= nuevo_g:
                    continue

                nuevo_h = calcular_h(nuevos_pendientes, nuevo_tiempo_simulado,
                                      pesos_estaticos, pesos_dinamicos, tasas_lambda)

                heapq.heappush(frontera, EstadoNodo(
                    agenda_parcial=nueva_agenda, pacientes_pendientes=nuevos_pendientes,
                    tiempo_restante=nuevo_tiempo_restante, tiempo_simulado_actual=nuevo_tiempo_simulado,
                    g=nuevo_g, h=nuevo_h, w=w
                ))

        if len(frontera) > 5000:
            frontera = heapq.nsmallest(5000, frontera)

    return None
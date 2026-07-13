"""
 SIMULACION — Driver semanal genérico para algoritmos basados en DataFrame
Ambos baselines basados en pandas (Greedy y FIFO) comparten exactamente la
misma mecánica de simulación multi-semana que ya usa Weighted A* en cada semana 
se arma una agenda con los pacientes pendientes, se retiran los agendados, y se avanza en
`dias_postergacion` días la espera de los que quedaron pendientes (lo que
recalcula automáticamente su score dinámico y vulnerabilidad la próxima vez
que se evalúan, porque scoring.py lee `dias_en_lista` directamente de la fila).

Este módulo centraliza esa mecánica para que Greedy/main.py y FIFO/main.py no
dupliquen el loop, y para que Evaluacion/evaluacion_comparativa.py pueda
correr los tres algoritmos (FIFO, Greedy, wA*) bajo condiciones idénticas.

"""

import time
from typing import Callable, Optional

import pandas as pd

from scoring import score_dinamico, vulnerabilidad


def simular_semanas_df(
    df_inicial: pd.DataFrame,
    seleccionar_fn: Callable[[pd.DataFrame, float, int], pd.DataFrame],
    horas_pabellon: float,
    dias_postergacion: int = 7,
    n_semanas: int = 60,
    top_k_candidatos: Optional[int] = None,
    nombre_algoritmo: str = "Algoritmo",
    verbose: bool = True,
):
    """
    Ejecuta `seleccionar_fn` semana a semana sobre `df_inicial` hasta que no
    queden pacientes pendientes o se alcance `n_semanas` (tope de seguridad).

    seleccionar_fn(df_candidatos, horas_disponibles, dias_postergacion) debe
    devolver un DataFrame con los pacientes seleccionados esa semana (debe
    incluir al menos la columna "id_paciente" y "dias_en_lista").

    Devuelve (historial, pendientes_finales, metricas).
    """
    pendientes = df_inicial.copy().reset_index(drop=True)
    historial = []
    tiempos_semana = []
    total_agendados = 0
    suma_dias_al_agendar = 0.0

    for semana in range(1, n_semanas + 1):
        if pendientes.empty:
            if verbose:
                print(f"[{nombre_algoritmo}] Todos los pacientes fueron agendados antes de la semana {semana}.")
            break

        candidatos = pendientes
        if top_k_candidatos is not None and len(candidatos) > top_k_candidatos:
            # Poda la RAMA de decisión de esta semana (no la población): se
            # ordena por score_dinamico actual (dias_extra=0) y se toman los
            # top_k_candidatos con mayor riesgo/prioridad. Los que quedan
            # fuera siguen en `pendientes` y compiten de nuevo la próxima
            # semana con más días de espera acumulados.
            candidatos = candidatos.copy()
            candidatos["_score_tmp"] = candidatos.apply(
                lambda fila: score_dinamico(fila.to_dict(), dias_extra=0), axis=1
            )
            candidatos = (
                candidatos.sort_values("_score_tmp", ascending=False)
                .head(top_k_candidatos)
                .drop(columns="_score_tmp")
            )

        t0 = time.perf_counter()
        seleccion = seleccionar_fn(candidatos, horas_pabellon, dias_postergacion)
        t1 = time.perf_counter()
        tiempos_semana.append(t1 - t0)

        if seleccion is None or seleccion.empty:
            ids_sel = set()
        else:
            ids_sel = set(seleccion["id_paciente"])
            total_agendados += len(seleccion)
            suma_dias_al_agendar += seleccion["dias_en_lista"].sum()

        if verbose:
            print(f"[{nombre_algoritmo}] Semana {semana}: agendados {len(ids_sel)} "
                  f"| pendientes al inicio {len(pendientes)} "
                  f"| tiempo de cómputo: {t1 - t0:.3f}s")

        pendientes = pendientes[~pendientes["id_paciente"].isin(ids_sel)].reset_index(drop=True)
        if not pendientes.empty:
            pendientes["dias_en_lista"] = pendientes["dias_en_lista"] + dias_postergacion

        # Vulnerables que quedan EN COLA esta semana (mismo criterio vp(t)>=1
        # que se usa para la métrica final, pero evaluado semana a semana en
        # vez de una sola vez al término de la simulación).
        if not pendientes.empty:
            vulnerabilidades_semana = pendientes.apply(
                lambda fila: vulnerabilidad(fila.to_dict(), 0), axis=1
            )
            vulnerables_en_cola = int((vulnerabilidades_semana >= 1).sum())
        else:
            vulnerables_en_cola = 0

        historial.append({
            "semana": semana,
            "agendados": len(ids_sel),
            "pendientes_restantes": len(pendientes),
            "vulnerables_en_cola": vulnerables_en_cola,
            "tiempo_seg": t1 - t0,
        })

    if not pendientes.empty:
        vulnerabilidades = pendientes.apply(lambda fila: vulnerabilidad(fila.to_dict(), 0), axis=1)
        pacientes_vulnerables = int((vulnerabilidades >= 1).sum())
    else:
        pacientes_vulnerables = 0

    metricas = {
        "algoritmo": nombre_algoritmo,
        "semanas_ejecutadas": len(historial),
        "pacientes_agendados": total_agendados,
        "pacientes_pendientes_final": len(pendientes),
        "promedio_dias_espera_al_agendar": (
            suma_dias_al_agendar / total_agendados if total_agendados else float("nan")
        ),
        "pacientes_vulnerables_sin_operar": pacientes_vulnerables,
        "tiempo_computo_total_seg": sum(tiempos_semana),
        "tiempo_computo_promedio_seg_por_semana": (
            sum(tiempos_semana) / len(tiempos_semana) if tiempos_semana else 0.0
        ),
    }

    return historial, pendientes, metricas
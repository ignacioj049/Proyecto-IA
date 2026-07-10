import pandas as pd

from scoring import score_dinamico


def _riesgo_paciente(fila: pd.Series, dias_extra: int = 0, calcular_riesgo=None) -> float:
    """
    Calcula el riesgo/costo dinámico del paciente.

    dias_extra representa días adicionales de espera clínica.
    No se usan minutos de pabellón como días.
    """
    paciente = fila.to_dict()

    if calcular_riesgo is not None:
        return calcular_riesgo(paciente, dias_extra)

    return score_dinamico(paciente, dias_extra=dias_extra)


def _costo_pendientes(
    df_pendientes: pd.DataFrame,
    dias_extra: int,
    calcular_riesgo=None,
) -> float:
    """
    Estima el costo de dejar pendientes a los pacientes restantes.
    """
    costo = 0.0

    for _, paciente in df_pendientes.iterrows():
        costo += _riesgo_paciente(paciente, dias_extra, calcular_riesgo)

    return costo


def greedy_priorizacion(
    df: pd.DataFrame,
    horas_disponibles: float,
    dias_postergacion: int = 7,
    calcular_riesgo=None,
) -> pd.DataFrame:
    """
    Greedy basado en minimización local del deterioro acumulado.

    En cada iteración evalúa cada paciente factible y selecciona aquel que
    genera el menor costo total estimado:

        costo = costo_acumulado
              + riesgo_del_paciente_agendado_ahora
              + riesgo_estimado_de_los_pacientes_pendientes_en_la_siguiente_semana

    La proyección temporal se hace en días de espera, no en minutos de cirugía.
    """

    pendientes = df.copy()
    seleccionados = []

    tiempo_restante_horas = horas_disponibles
    costo_acumulado = 0.0

    while not pendientes.empty:
        mejor_idx = None
        mejor_costo_estimado = float("inf")
        mejor_riesgo = None

        for idx, paciente in pendientes.iterrows():
            duracion_horas = paciente["duracion_cirugia_horas"]

            if duracion_horas > tiempo_restante_horas:
                continue

            riesgo_actual = _riesgo_paciente(
                paciente,
                dias_extra=0,
                calcular_riesgo=calcular_riesgo,
            )

            pendientes_sin_paciente = pendientes.drop(index=idx)

            costo_futuro = _costo_pendientes(
                pendientes_sin_paciente,
                dias_extra=dias_postergacion,
                calcular_riesgo=calcular_riesgo,
            )

            costo_estimado = costo_acumulado + riesgo_actual + costo_futuro

            if costo_estimado < mejor_costo_estimado:
                mejor_idx = idx
                mejor_costo_estimado = costo_estimado
                mejor_riesgo = riesgo_actual

        if mejor_idx is None:
            break

        paciente_seleccionado = pendientes.loc[mejor_idx].copy()
        duracion_horas = paciente_seleccionado["duracion_cirugia_horas"]

        paciente_seleccionado["riesgo_asignacion"] = mejor_riesgo
        paciente_seleccionado["costo_estimado_greedy"] = mejor_costo_estimado
        paciente_seleccionado["horas_restantes_antes"] = tiempo_restante_horas
        paciente_seleccionado["horas_restantes_despues"] = (
            tiempo_restante_horas - duracion_horas
        )

        seleccionados.append(paciente_seleccionado)

        costo_acumulado += mejor_riesgo
        tiempo_restante_horas -= duracion_horas
        pendientes = pendientes.drop(index=mejor_idx)

    return pd.DataFrame(seleccionados)
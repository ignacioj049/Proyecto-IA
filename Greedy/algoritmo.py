import pandas as pd

from generar_pacientes import score_dinamico


def _riesgo_paciente(fila: pd.Series, dias_extra: float) -> float:
    """
    Calcula el riesgo/costo dinámico del paciente si se agenda después
    de dias_extra días adicionales de espera.
    """
    paciente = fila.to_dict()
    return score_dinamico(paciente, dias_extra=dias_extra)


def _costo_pendientes(df_pendientes: pd.DataFrame, dias_extra: float) -> float:
    """
    Estima el costo futuro de dejar pendientes a los pacientes restantes.
    Esta función cumple un rol similar a h(n) en wA*.
    """
    costo = 0.0

    for _, paciente in df_pendientes.iterrows():
        costo += _riesgo_paciente(paciente, dias_extra)

    return costo


def greedy_priorizacion(
    df: pd.DataFrame,
    horas_disponibles: float,
    minutos_por_dia_espera: int = 480,
) -> pd.DataFrame:
    """
    Greedy basado en minimización de deterioro acumulado.

    En cada iteración evalúa cada paciente factible y selecciona aquel que
    genera el menor costo total estimado:

        costo = costo_acumulado
              + riesgo_del_paciente_agendado_ahora
              + riesgo_estimado_de_los_pacientes_pendientes

    Esto aproxima la lógica del wA*, pero sin explorar todo el árbol de búsqueda.
    """

    pendientes = df.copy()
    seleccionados = []

    tiempo_restante_horas = horas_disponibles
    tiempo_simulado_minutos = 0.0
    costo_acumulado = 0.0

    while not pendientes.empty:
        mejor_idx = None
        mejor_costo_estimado = float("inf")
        mejor_riesgo = None
        mejor_dias_extra = None

        for idx, paciente in pendientes.iterrows():
            duracion_horas = paciente["duracion_cirugia_horas"]

            if duracion_horas > tiempo_restante_horas:
                continue

            duracion_minutos = duracion_horas * 60

            # Convertimos minutos de agenda a días de espera.
            # 480 min = 1 jornada quirúrgica de 8 horas.
            dias_extra_actual = tiempo_simulado_minutos / minutos_por_dia_espera
            dias_extra_futuro = (tiempo_simulado_minutos + duracion_minutos) / minutos_por_dia_espera

            riesgo_actual = _riesgo_paciente(paciente, dias_extra_actual)

            pendientes_sin_paciente = pendientes.drop(index=idx)
            costo_futuro = _costo_pendientes(pendientes_sin_paciente, dias_extra_futuro)

            costo_estimado = costo_acumulado + riesgo_actual + costo_futuro

            if costo_estimado < mejor_costo_estimado:
                mejor_idx = idx
                mejor_costo_estimado = costo_estimado
                mejor_riesgo = riesgo_actual
                mejor_dias_extra = dias_extra_actual

        if mejor_idx is None:
            break

        paciente_seleccionado = pendientes.loc[mejor_idx].copy()
        duracion_horas = paciente_seleccionado["duracion_cirugia_horas"]
        duracion_minutos = duracion_horas * 60

        paciente_seleccionado["dias_extra_asignacion"] = mejor_dias_extra
        paciente_seleccionado["riesgo_asignacion"] = mejor_riesgo
        paciente_seleccionado["costo_estimado_greedy"] = mejor_costo_estimado
        paciente_seleccionado["horas_restantes_antes"] = tiempo_restante_horas
        paciente_seleccionado["horas_restantes_despues"] = tiempo_restante_horas - duracion_horas

        seleccionados.append(paciente_seleccionado)

        costo_acumulado += mejor_riesgo
        tiempo_restante_horas -= duracion_horas
        tiempo_simulado_minutos += duracion_minutos

        pendientes = pendientes.drop(index=mejor_idx)

    return pd.DataFrame(seleccionados)
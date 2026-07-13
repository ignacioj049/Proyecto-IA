import pandas as pd

from scoring import score_dinamico, vulnerabilidad


def _riesgo_paciente(
    fila: pd.Series,
    dias_extra: int = 0,
    calcular_riesgo=None,
) -> float:
    """
    Calcula el riesgo/costo dinámico del paciente.

    dias_extra representa días adicionales de espera clínica.
    No se convierten minutos de pabellón a días.
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
        costo += _riesgo_paciente(
            paciente,
            dias_extra=dias_extra,
            calcular_riesgo=calcular_riesgo,
        )

    return costo


def greedy_priorizacion(
    df: pd.DataFrame,
    horas_disponibles: float,
    dias_postergacion: int = 7,
    calcular_riesgo=None,
    top_k_candidatos: int | None = None,
) -> pd.DataFrame:
 
    pendientes = df.copy()

    if top_k_candidatos is not None and len(pendientes) > top_k_candidatos:
        riesgos_actuales = pendientes.apply(
            lambda fila: _riesgo_paciente(fila, dias_extra=0, calcular_riesgo=calcular_riesgo),
            axis=1,
        )
        pendientes = pendientes.loc[
            riesgos_actuales.sort_values(ascending=False).index
        ].head(top_k_candidatos)

    seleccionados = []

    tiempo_restante_horas = horas_disponibles
    costo_acumulado = 0.0

    while not pendientes.empty:
        mejor_idx = None
        mejor_costo_estimado = float("inf")
        mejor_riesgo = None
        mejor_costo_pendientes = None

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

            costo_pendientes = _costo_pendientes(
                pendientes_sin_paciente,
                dias_extra=dias_postergacion,
                calcular_riesgo=calcular_riesgo,
            )

            costo_estimado = (
                costo_acumulado
                + riesgo_actual
                + costo_pendientes
            )

            if costo_estimado < mejor_costo_estimado:
                mejor_idx = idx
                mejor_costo_estimado = costo_estimado
                mejor_riesgo = riesgo_actual
                mejor_costo_pendientes = costo_pendientes

        if mejor_idx is None:
            break

        paciente_seleccionado = pendientes.loc[mejor_idx].copy()
        duracion_horas = paciente_seleccionado["duracion_cirugia_horas"]

        paciente_seleccionado["riesgo_asignacion"] = mejor_riesgo
        paciente_seleccionado["costo_pendientes_estimado"] = mejor_costo_pendientes
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


ORDEN_GRUPOS_PAPER = [
    (1, "A"), (1, "B"), (1, "C"),
    (2, "A"), (2, "B"), (2, "C"),
    (3, "A"), (3, "B"), (3, "C"),
    (4, "A"), (4, "B"), (4, "C"),
]


def _clasificar_grupo_paper(fila: pd.Series, score_promedio: float) -> int:
    """Clasifica un paciente en los 4 cuadrantes de la Sección 3.5 del paper:
    Grupo 1: score>=promedio y v>=1 | Grupo 2: score>=promedio y v<1
    Grupo 3: score<promedio y v>=1  | Grupo 4: score<promedio y v<1
    """
    alto = fila["_score_dinamico"] >= score_promedio
    vulnerable = fila["_vulnerabilidad"] >= 1
    if alto and vulnerable:
        return 1
    if alto and not vulnerable:
        return 2
    if not alto and vulnerable:
        return 3
    return 4


def greedy_priorizacion_paper(
    df: pd.DataFrame,
    horas_disponibles: float,
    dias_postergacion: int = 7,
) -> pd.DataFrame:
    pendientes = df.copy()
    if pendientes.empty:
        return pd.DataFrame()

    pendientes["_score_dinamico"] = pendientes.apply(
        lambda fila: score_dinamico(fila.to_dict(), dias_extra=0), axis=1
    )
    pendientes["_vulnerabilidad"] = pendientes.apply(
        lambda fila: vulnerabilidad(fila.to_dict(), dias_extra=0), axis=1
    )

    score_promedio = pendientes["_score_dinamico"].mean()
    pendientes["_grupo"] = pendientes.apply(
        lambda fila: _clasificar_grupo_paper(fila, score_promedio), axis=1
    )

    tiempo_restante_horas = horas_disponibles
    seleccionados = []

    for grupo, tipo in ORDEN_GRUPOS_PAPER:
        if tiempo_restante_horas <= 0:
            break

        bucket = pendientes[
            (pendientes["_grupo"] == grupo) & (pendientes["tipo_diagnostico"] == tipo)
        ].sort_values("_score_dinamico", ascending=False)

        for idx, paciente in bucket.iterrows():
            duracion_horas = paciente["duracion_cirugia_horas"]
            if duracion_horas > tiempo_restante_horas:
                continue

            fila_seleccionada = paciente.copy()
            fila_seleccionada["riesgo_asignacion"] = paciente["_score_dinamico"]
            fila_seleccionada["vulnerabilidad_asignacion"] = paciente["_vulnerabilidad"]
            fila_seleccionada["grupo_paper"] = grupo
            fila_seleccionada["horas_restantes_antes"] = tiempo_restante_horas
            tiempo_restante_horas -= duracion_horas
            fila_seleccionada["horas_restantes_despues"] = tiempo_restante_horas

            seleccionados.append(fila_seleccionada)
            pendientes = pendientes.drop(index=idx)

    if not seleccionados:
        return pd.DataFrame()

    resultado = pd.DataFrame(seleccionados)
    return resultado.drop(columns=["_score_dinamico", "_vulnerabilidad", "_grupo"], errors="ignore")
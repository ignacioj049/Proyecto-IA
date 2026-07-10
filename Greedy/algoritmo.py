import pandas as pd

PRIORIDAD_TIPO_DIAGNOSTICO = {
    "A": 1,
    "B": 2,
    "C": 3,
}


def greedy_priorizacion(df: pd.DataFrame, horas_disponibles: float) -> pd.DataFrame:
    df = df.copy()
    df["prioridad_tipo"] = df["tipo_diagnostico"].map(PRIORIDAD_TIPO_DIAGNOSTICO)

    pacientes_ordenados = df.sort_values(
        by=[
            "grupo_prioridad",
            "prioridad_tipo",
            "vulnerabilidad",
            "score_dinamico",
        ],
        ascending=[
            True,
            True,
            False,
            False,
        ],
    )

    seleccionados = []
    horas_restantes = horas_disponibles

    for _, paciente in pacientes_ordenados.iterrows():
        duracion = paciente["duracion_cirugia_horas"]

        if duracion <= horas_restantes:
            paciente = paciente.copy()
            paciente["horas_restantes_antes"] = horas_restantes
            paciente["horas_restantes_despues"] = horas_restantes - duracion
            seleccionados.append(paciente)
            horas_restantes -= duracion

    return pd.DataFrame(seleccionados)
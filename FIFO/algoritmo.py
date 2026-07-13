"""
 FIFO — orden estricto de llegada
Agenda a los pacientes exclusivamente por cuánto tiempo llevan esperando
(mayor dias_en_lista primero), sin considerar score dinámico, vulnerabilidad,
severidad clínica ni ningún otro criterio biopsicosocial, y sirve como punto de
referencia mínimo, ya que cualquier algoritmo que use información clínica debería
superar a este baseline en pacientes vulnerables sin operar, aunque puede que
no siempre en promedio de días de espera (FIFO, por diseño, minimiza esa
métrica en particular).
"""

import pandas as pd

from scoring import score_dinamico


def fifo_priorizacion(
    df: pd.DataFrame,
    horas_disponibles: float,
    dias_postergacion: int = 7,
) -> pd.DataFrame:
    """
    Selecciona pacientes en orden estricto de llegada (mayor dias_en_lista
    primero) hasta llenar la capacidad de pabellón disponible.

    `dias_postergacion` no se usa dentro de esta función (FIFO no proyecta
    ningún costo futuro); se mantiene en la firma por compatibilidad con el
    driver genérico de simulacion.simular_semanas_df.
    """
    if df.empty:
        return pd.DataFrame()

    candidatos = df.sort_values(by="dias_en_lista", ascending=False)

    tiempo_restante_horas = horas_disponibles
    seleccionados = []

    for idx, paciente in candidatos.iterrows():
        duracion_horas = paciente["duracion_cirugia_horas"]
        if duracion_horas > tiempo_restante_horas:
            continue

        fila_seleccionada = paciente.copy()
        # Riesgo dinámico calculado solo con fines informativos/comparativos
        # (no influye en la selección: FIFO ordena únicamente por antigüedad).
        fila_seleccionada["riesgo_asignacion"] = score_dinamico(
            paciente.to_dict(), dias_extra=0
        )
        fila_seleccionada["horas_restantes_antes"] = tiempo_restante_horas
        tiempo_restante_horas -= duracion_horas
        fila_seleccionada["horas_restantes_despues"] = tiempo_restante_horas

        seleccionados.append(fila_seleccionada)

    if not seleccionados:
        return pd.DataFrame()

    return pd.DataFrame(seleccionados)

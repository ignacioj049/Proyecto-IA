import sys
from pathlib import Path

import pandas as pd

# Agrega la carpeta raíz del proyecto al path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from generar_pacientes import generar_pacientes

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
            True,   # grupo 1 antes que 2, 3, 4
            True,   # tipo A antes que B y C
            False,  # mayor vulnerabilidad primero
            False,  # mayor score dinámico primero
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

        if horas_restantes <= 0:
            break

    return pd.DataFrame(seleccionados)

if __name__ == "__main__":
    df = generar_pacientes(n=200, semilla=42)

    horas_pabellon = 8.0
    seleccion = greedy_priorizacion(df, horas_pabellon)

    columnas = [
        "id_paciente",
        "Diag",
        "tipo_diagnostico",
        "grupo_prioridad",
        "score_dinamico",
        "vulnerabilidad",
        "duracion_cirugia_horas",
        "horas_restantes_antes",
        "horas_restantes_despues",
    ]

    print("\nPacientes seleccionados por greedy:\n")
    print(seleccion[columnas].to_string(index=False))

    horas_usadas = seleccion["duracion_cirugia_horas"].sum()
    horas_restantes = horas_pabellon - horas_usadas
    uso_pabellon = horas_usadas / horas_pabellon * 100

    print("\nResumen:")
    print(f"Horas disponibles: {horas_pabellon}")
    print(f"Horas usadas: {horas_usadas:.2f}")
    print(f"Horas restantes: {horas_restantes:.2f}")
    print(f"Uso de pabellón: {uso_pabellon:.1f}%")
    print(f"Pacientes seleccionados: {len(seleccion)}")

    # Guardar selección en CSV
    seleccion[columnas].to_csv(
        "Greedy/seleccion_greedy.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nSelección guardada en: Greedy/seleccion_greedy.csv")
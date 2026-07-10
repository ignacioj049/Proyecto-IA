import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from generar_pacientes import generar_pacientes
from Greedy.algoritmo import greedy_priorizacion


def main():
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
    "riesgo_asignacion",
    "costo_estimado_greedy",
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

    salida = Path(__file__).resolve().parent / "seleccion_greedy.csv"
    seleccion[columnas].to_csv(salida, index=False, encoding="utf-8-sig")
    print(f"\nSelección guardada en: {salida}")


if __name__ == "__main__":
    main()
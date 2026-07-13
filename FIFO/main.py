import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from generar_pacientes import generar_pacientes
from FIFO.algoritmo import fifo_priorizacion
from simulacion import simular_semanas_df


def main():
    df = generar_pacientes(n=200, semilla=42)

    horas_pabellon = 8.0
    dias_postergacion = 7
    n_semanas = 60  # tope de seguridad

    def seleccionar_semana(df_candidatos, horas_disponibles, dias_postergacion):
        return fifo_priorizacion(
            df_candidatos,
            horas_disponibles=horas_disponibles,
            dias_postergacion=dias_postergacion,
        )

    print("Iniciando simulación FIFO multi-semana (baseline ingenuo)...")
    print(f"Parámetros: horas_pabellon={horas_pabellon}h | "
          f"dias_postergacion={dias_postergacion} | n_semanas(tope)={n_semanas}\n")

    
    historial, pendientes_finales, metricas = simular_semanas_df(
        df,
        seleccionar_semana,
        horas_pabellon=horas_pabellon,
        dias_postergacion=dias_postergacion,
        n_semanas=n_semanas,
        top_k_candidatos=None,
        nombre_algoritmo="FIFO",
    )

    print("\n" + "=" * 55)
    print("RESUMEN DE LA SIMULACIÓN FIFO")
    print("=" * 55)
    print(f"Semanas simuladas: {metricas['semanas_ejecutadas']}")
    print(f"Total pacientes agendados: {metricas['pacientes_agendados']}/{len(df)}")
    print(f"Pacientes sin agendar al final: {metricas['pacientes_pendientes_final']}")
    print(f"Pacientes vulnerables (vp>=1) sin operar: {metricas['pacientes_vulnerables_sin_operar']}")
    print(f"Promedio de días de espera al momento de agendar: "
          f"{metricas['promedio_dias_espera_al_agendar']:.1f}")
    print(f"Tiempo de cómputo total: {metricas['tiempo_computo_total_seg']:.2f}s "
          f"({metricas['tiempo_computo_promedio_seg_por_semana']:.3f}s/semana en promedio)")
    print("=" * 55 + "\n")

    salida = Path(__file__).resolve().parent / "seleccion_fifo.csv"
    pd.DataFrame(historial).to_csv(salida, index=False, encoding="utf-8-sig")
    print(f"Historial semanal guardado en: {salida}")


if __name__ == "__main__":
    main()

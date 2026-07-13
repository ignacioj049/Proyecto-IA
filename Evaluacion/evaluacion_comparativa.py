"""
    Evaluación comparativa: FIFO vs Greedy vs wA*
Corre los TRES enfoques planificados (ver diapositiva "Experimentos
planificados" de la presentación) bajo condiciones idénticas:
- mismo dataset de pacientes (misma semilla, mismo n=200)
- misma capacidad de pabellón (horas/minutos equivalentes)
- misma simulación multi-semana (se agenda semana a semana, se retira a los
  agendados, se avanzan +dias_postergacion días a los pendientes)
- mismo top_k_candidatos como límite de RAMA de decisión por semana (no de
  población) para los algoritmos que lo necesitan por costo computacional
- mismas lambdas / pesos / alphas (todos usan config_modelo.py y scoring.py)

Los tres algoritmos comparados:
  1. FIFO            — baseline ingenuo, orden estricto de llegada (FIFO/algoritmo.py)
  2. Greedy          — replica fiel de la Sección 3.5 del paper: grupos
                         1-4 x tipo de diagnóstico A/B/C (Greedy/algoritmo.py:
                         greedy_priorizacion_paper)
  3. Weighted A*      — nuestra propuesta: búsqueda que minimiza el riesgo
                         acumulado total de la agenda (W_A_estrella/algoritmo.py)


Para cada algoritmo se miden las 3 métricas de evaluación planificadas:
  1. Promedio de días de espera al momento de agendar (aproxima el aswl(t)
     del paper, pero medido sobre los pacientes efectivamente agendados)
  2. Número de pacientes vulnerables (vp(t) >= 1) que quedan sin operar
  3. Tiempo de cómputo (total y promedio por semana)

Además de esas métricas finales, se arma una segunda tabla semana a semana
que compara cuántos pacientes vulnerables quedan EN COLA en cada momento de
la simulación (no solo al cierre). Con n=200 los tres algoritmos terminan
agendando a todos los pacientes, por lo que la métrica final #2 da 0 para
los tres y no alcanza a distinguirlos: la evolución semana a semana sí lo
hace, porque muestra si un algoritmo deja acumularse pacientes vulnerables
durante la simulación aunque al final los alcance a operar a todos.
"""

import sys
from pathlib import Path

import pandas as pd

# Configuración de paths
RAIZ = Path(__file__).resolve().parents[1]
CARPETA_WASTAR = RAIZ / "W_A_estrella"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(CARPETA_WASTAR))

from generar_pacientes import generar_pacientes
from simulacion import simular_semanas_df
from FIFO.algoritmo import fifo_priorizacion
from Greedy.algoritmo import greedy_priorizacion_paper

# El módulo wA* usa imports relativos a su propia carpeta (modelos, traductor,
# algoritmo), por eso se agregó W_A_estrella al sys.path antes de importar.
import main as wastar_main

# Parámetros del experimento (idénticos para los tres algoritmos)
N_PACIENTES = 200
SEMILLA = 42
HORAS_PABELLON = 8.0
TOP_K_CANDIDATOS = 40   # límite de RAMA de decisión por semana, no de población
PESO_W = 2.0            # w del f(n) = g(n) + w*h(n) de wA*
DIAS_POSTERGACION = 7   # si no se agenda ahora, el paciente espera 1 semana más
N_SEMANAS_TOPE = 60     # tope de seguridad; en la práctica todos terminan bastante antes


def dataframe_a_pacientes_wastar(df: pd.DataFrame):
    """Adaptador: DataFrame de pacientes -> objetos Paciente (formato wA*)."""
    from modelos import Paciente
    from traductor import traducir_valor

    pacientes = []
    for _, p in df.iterrows():
        tiempo_minutos = int(p["duracion_cirugia_horas"] * 60)
        vars_estaticas = {k: traducir_valor(k, p[k]) for k in wastar_main.COLS_ESTATICAS}
        vars_dinamicas = {k: traducir_valor(k, p[k]) for k in wastar_main.COLS_DINAMICAS}
        pacientes.append(Paciente(
            id_paciente=p["id_paciente"],
            tiempo_quirurgico=tiempo_minutos,
            vars_estaticas=vars_estaticas,
            vars_dinamicas=vars_dinamicas,
            tipo_diag=p["tipo_diagnostico"],
            dias_espera_base=p["dias_en_lista"],
            jclin_meses=p.get("Jclin_meses"),
        ))
    return pacientes


def ejecutar_fifo(df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Corre FIFO y devuelve (historial_semanal, metricas_finales)."""
    def seleccionar_semana(df_candidatos, horas_disponibles, dias_postergacion):
        return fifo_priorizacion(df_candidatos, horas_disponibles, dias_postergacion)

    historial, _, metricas = simular_semanas_df(
        df, seleccionar_semana, horas_pabellon=HORAS_PABELLON,
        dias_postergacion=DIAS_POSTERGACION, n_semanas=N_SEMANAS_TOPE,
        top_k_candidatos=None, nombre_algoritmo="FIFO", verbose=False,
    )
    return historial, metricas


def ejecutar_greedy_paper(df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Corre Greedy (paper) y devuelve (historial_semanal, metricas_finales)."""
    def seleccionar_semana(df_candidatos, horas_disponibles, dias_postergacion):
        return greedy_priorizacion_paper(df_candidatos, horas_disponibles, dias_postergacion)

    historial, _, metricas = simular_semanas_df(
        df, seleccionar_semana, horas_pabellon=HORAS_PABELLON,
        dias_postergacion=DIAS_POSTERGACION, n_semanas=N_SEMANAS_TOPE,
        top_k_candidatos=TOP_K_CANDIDATOS, nombre_algoritmo="Greedy (paper)", verbose=False,
    )
    return historial, metricas


def ejecutar_wastar(df: pd.DataFrame) -> tuple[list[dict], dict]:
    """Corre Weighted A* y devuelve (historial_semanal, metricas_finales)."""
    pacientes = dataframe_a_pacientes_wastar(df)
    historial, _, metricas = wastar_main.simular_semanas(
        pacientes,
        capacidad_quirofano_minutos=int(HORAS_PABELLON * 60),
        peso_w=PESO_W,
        top_k=TOP_K_CANDIDATOS,
        dias_postergacion=DIAS_POSTERGACION,
        n_semanas=N_SEMANAS_TOPE,
        verbose=False,
    )
    return historial, metricas


def construir_tabla_semanal_comparativa(
    historiales: dict[str, list[dict]],
    columna: str,
) -> pd.DataFrame:
    """
    Arma una tabla semana a semana con una columna por algoritmo, comparando
    `columna` (p.ej. "vulnerables_en_cola") entre los algoritmos pasados en
    `historiales`.

    historiales: {"FIFO": historial_fifo, "Greedy (paper)": historial_greedy,
                  "Weighted A*": historial_wastar}. Cada historial_x es la
    lista de dicts semanales que devuelven simulacion.simular_semanas_df y
    W_A_estrella.main.simular_semanas (una vez agregado el campo `columna`
    a esos historiales).

    Los algoritmos pueden terminar en distintas semanas (uno puede agendar a
    todos sus pacientes antes que otro). Se hace un merge "outer" por
    semana, y las semanas posteriores al término de un algoritmo -que ya no
    tiene entradas en su historial porque no le quedan pacientes
    pendientes- se rellenan con 0: si no queda nadie pendiente, tampoco
    queda nadie vulnerable en cola.
    """
    tabla = None
    for nombre_algoritmo, historial in historiales.items():
        if historial:
            columna_df = pd.DataFrame(historial)[["semana", columna]].rename(
                columns={columna: nombre_algoritmo}
            )
        else:
            columna_df = pd.DataFrame(columns=["semana", nombre_algoritmo])

        tabla = columna_df if tabla is None else tabla.merge(columna_df, on="semana", how="outer")

    tabla = tabla.sort_values("semana").reset_index(drop=True)
    columnas_algoritmos = [c for c in tabla.columns if c != "semana"]
    tabla[columnas_algoritmos] = tabla[columnas_algoritmos].fillna(0).astype(int)
    tabla["semana"] = tabla["semana"].astype(int)

    return tabla.set_index("semana")


def main():
    print("=" * 70)
    print("EVALUACION COMPARATIVA — FIFO vs Greedy (paper) vs Weighted A*")
    print("=" * 70)
    print(f"Dataset: n={N_PACIENTES}, semilla={SEMILLA} (población COMPLETA, sin recorte previo)")
    print(f"Capacidad de pabellón: {HORAS_PABELLON}h/semana")
    print(f"top_k_candidatos (rama de decisión por semana): {TOP_K_CANDIDATOS} | "
          f"w (wA*): {PESO_W} | dias_postergacion: {DIAS_POSTERGACION}")
    print("=" * 70)

    # Mismo dataset de 200 pacientes para los tres algoritmos.
    df = generar_pacientes(n=N_PACIENTES, semilla=SEMILLA)

    print("\n>> Ejecutando FIFO...")
    historial_fifo, resultado_fifo = ejecutar_fifo(df.copy())

    print(">> Ejecutando Greedy (replicación del paper)...")
    historial_greedy, resultado_greedy = ejecutar_greedy_paper(df.copy())

    print(">> Ejecutando Weighted A*...")
    historial_wastar, resultado_wastar = ejecutar_wastar(df.copy())

    # ------------------------------------------------------------------
    # Tabla 1: métricas finales (igual que antes)
    # ------------------------------------------------------------------
    tabla = pd.DataFrame([resultado_fifo, resultado_greedy, resultado_wastar]).set_index("algoritmo")

    columnas_orden = [
        "promedio_dias_espera_al_agendar",
        "pacientes_vulnerables_sin_operar",
        "tiempo_computo_total_seg",
        "tiempo_computo_promedio_seg_por_semana",
        "semanas_ejecutadas",
        "pacientes_agendados",
        "pacientes_pendientes_final",
    ]
    tabla = tabla[columnas_orden]

    print("\n" + "=" * 70)
    print("TABLA COMPARATIVA (métricas finales)")
    print("=" * 70)
    print(tabla.to_string())

    # ------------------------------------------------------------------
    # Tabla 2: vulnerables EN COLA, semana a semana (NUEVO)
    # ------------------------------------------------------------------
    historiales = {
        "FIFO": historial_fifo,
        "Greedy (paper)": historial_greedy,
        "Weighted A*": historial_wastar,
    }
    tabla_semanal = construir_tabla_semanal_comparativa(historiales, columna="vulnerables_en_cola")

    print("\n" + "=" * 70)
    print("TABLA SEMANAL — vulnerables en cola (vp(t) >= 1), por semana")
    print("=" * 70)
    print(tabla_semanal.to_string())

    # Guardar resultados
    salida_csv = Path(__file__).resolve().parent / "tabla_comparativa.csv"
    salida_md = Path(__file__).resolve().parent / "tabla_comparativa.md"
    tabla.to_csv(salida_csv, encoding="utf-8-sig")
    with open(salida_md, "w", encoding="utf-8") as f:
        f.write(tabla.to_markdown())

    salida_semanal_csv = Path(__file__).resolve().parent / "tabla_semanal_vulnerables.csv"
    salida_semanal_md = Path(__file__).resolve().parent / "tabla_semanal_vulnerables.md"
    tabla_semanal.to_csv(salida_semanal_csv, encoding="utf-8-sig")
    with open(salida_semanal_md, "w", encoding="utf-8") as f:
        f.write(tabla_semanal.to_markdown())

    print(f"\nTabla de métricas finales guardada en:\n  {salida_csv}\n  {salida_md}")
    print(f"Tabla semanal de vulnerables en cola guardada en:\n  {salida_semanal_csv}\n  {salida_semanal_md}")


if __name__ == "__main__":
    main()
"""
    Evaluación comparativa Greedy vs wA*

Script de evaluación común (ejecución de ambos algoritmos) bajo
exactamente las mismas condiciones:
- mismo dataset de pacientes (misma semilla, mismo n)
- misma capacidad de pabellón (horas/minutos equivalentes)
- mismo top_k de candidatos evaluados en cada paso (= 40)
- mismas lambdas / pesos/ alphas (ambos ya usan config_modelo.py y 
scoring.py)

Para cada uno mide:
- tiempo de ejecución (seg)
- cantidad de pacientes seleccionados / agendados
- horas usadas 
- horas restantes de pabellón
- costo total real de la agenda construida (suma del riesgi dinámico
de los pacientes efectivamente agendados, en el momento en que se
agendan)
"""

import sys 
import time
from pathlib import Path
import pandas as pd

#Configuración de paths
RAIZ = Path(__file__).resolve().parents[1]
CARPETA_WASTAR = RAIZ / "W_A_estrella"
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(CARPETA_WASTAR))

from generar_pacientes import generar_pacientes
from config_modelo import PESOS, VARIABLES_DEPENDIENTES_TIEMPO, LAMBDA_POR_TIPO
from Greedy.algoritmo import greedy_priorizacion

from modelos import Paciente
from traductor import traducir_valor
from algoritmo import weighted_a_star

#Parámetros del experimento (idénticos para ambos algoritmos)
N_PACIENTES = 200
SEMILLA = 42
HORAS_PABELLON = 8.0
TOP_K = 40
PESO_W = 2.0 # w del f(n) = g(n) + w*h(n) de wA*
DIAS_POSTERGACION = 7 #Si no se agenda ahora, espera 1 semana más 

CAPACIDAD_MINUTOS = int(HORAS_PABELLON*60)
COLS_ESTATICAS = [k for k in PESOS if k not in VARIABLES_DEPENDIENTES_TIEMPO]
COLS_DINAMICAS = [k for k in PESOS if k in VARIABLES_DEPENDIENTES_TIEMPO]
PESOS_ESTATICOS = {k: PESOS[k] for k in COLS_ESTATICAS}
PESOS_DINAMICOS = {k: PESOS[k] for k in COLS_DINAMICAS}


#Paso compartido: mismo top_40 para ambos algoritmos
def aplicar_top_k(df:pd.DataFrame, top_k:int) -> pd.DataFrame:
    """
    Replica el mismo criterio de preselección que Greedy/main.py y 
    W_A_estrella/main.py aplican por separado: ordenar por grupo_prioridad (asc),
    vulnerabilidad (desc) y score_dinámico (desc), y quedarse con los primeros
    top_k. Se  hace una sola vez aquí para garantizar que ambos algoritmos reciban
    exactamente el mismo subconjunto de pacientes
    """

    return df.sort_values(
        by=["grupo_prioridad", "vulnerabilidad", "score_dinamico"],
        ascending=[True, False, False],
    ).head(top_k).reset_index(drop=True)


#Adaptador: DataFrame de pacientes -> objetos Paciente (formato wA*)
def df_a_pacientes_wastar(df: pd.DataFrame) ->list:
    pacientes = []
    for _, p in df.iterrows():
        tiempo_minutos = int(p["duracion_cirugia_horas"]*60)
        vars_estaticas = {k: traducir_valor(k, p[k]) for k in COLS_ESTATICAS}
        vars_dinamicas = {k: traducir_valor(k, p[k]) for k in COLS_DINAMICAS}
        pacientes.append(Paciente(id_paciente = p["id_paciente"], 
                                  tiempo_quirurgico = tiempo_minutos, 
                                  vars_estaticas = vars_estaticas, 
                                  vars_dinamicas = vars_dinamicas,
                                  tipo_diag = p["tipo_diagnostico"],
                                  dias_espera_base = p["dias_en_lista"],))

    return pacientes


#Ejecución Greedy
def ejecutar_greedy(df_top_k: pd.DataFrame) -> dict:
    inicio = time.perf_counter()
    seleccion = greedy_priorizacion(df_top_k, horas_disponibles=HORAS_PABELLON, dias_postergacion=DIAS_POSTERGACION,)
    tiempo_ejecucion= time.perf_counter() - inicio

    horas_usadas = seleccion["duracion_cirugia_horas"].sum() if not seleccion.empty else 0.0
    costo_total = seleccion["riesgo_asignacion"].sum() if not seleccion.empty else 0.0
 
    return {
        "algoritmo": "Greedy",
        "tiempo_ejecucion_seg": round(tiempo_ejecucion, 4),
        "pacientes_seleccionados": len(seleccion),
        "horas_usadas": round(horas_usadas, 2),
        "horas_restantes": round(HORAS_PABELLON - horas_usadas, 2),
        "costo_total_agenda": round(costo_total, 4),
        "pacientes_agendados": len(seleccion),
    }


# Ejecución de Weighted A* (una sola pasada, sin simulación semanal)
def ejecutar_wastar(df_top_k: pd.DataFrame) -> dict:
    pacientes = df_a_pacientes_wastar(df_top_k)
 
    inicio = time.perf_counter()
    estado_final = weighted_a_star(
        pacientes_totales=pacientes,
        capacidad_quirurgica=CAPACIDAD_MINUTOS,
        w=PESO_W,
        pesos_estaticos=PESOS_ESTATICOS,
        pesos_dinamicos=PESOS_DINAMICOS,
        tasas_lambda=LAMBDA_POR_TIPO,
        top_k_candidatos=TOP_K,
        dias_postergacion=DIAS_POSTERGACION,
    )
    tiempo_ejecucion = time.perf_counter() - inicio
 
    if estado_final is None:
        return {
            "algoritmo": "Weighted A*",
            "tiempo_ejecucion_seg": round(tiempo_ejecucion, 4),
            "pacientes_seleccionados": 0,
            "horas_usadas": 0.0,
            "horas_restantes": HORAS_PABELLON,
            "costo_total_agenda": 0.0,
            "pacientes_agendados": 0,
        }
 
    agenda = estado_final.agenda_parcial
    minutos_usados = sum(p.tiempo_quirurgico for p in agenda)
    horas_usadas = minutos_usados / 60
 
    return {
        "algoritmo": "Weighted A*",
        "tiempo_ejecucion_seg": round(tiempo_ejecucion, 4),
        "pacientes_seleccionados": len(agenda),
        "horas_usadas": round(horas_usadas, 2),
        "horas_restantes": round(HORAS_PABELLON - horas_usadas, 2),
        "costo_total_agenda": round(estado_final.g, 4),
        "pacientes_agendados": len(agenda),
    }


# Orquestador principal
def main():
    print("=" * 70)
    print("EVALUACION COMPARATIVA — Greedy vs Weighted A*")
    print("=" * 70)
    print(f"Dataset: n={N_PACIENTES}, semilla={SEMILLA}")
    print(f"Capacidad de pabellón: {HORAS_PABELLON}h ({CAPACIDAD_MINUTOS} min)")
    print(f"top_k_candidatos: {TOP_K} | w (wA*): {PESO_W} | dias_postergacion:{DIAS_POSTERGACION}")
    print("=" * 70)
 
    # Mismo dataset para ambos algoritmos.
    df = generar_pacientes(n=N_PACIENTES, semilla=SEMILLA)

    df_top_k = aplicar_top_k(df, TOP_K)
    print(f"\nPacientes tras aplicar top_k = {TOP_K}: {len(df_top_k)}")
 
    print("\n>> Ejecutando Greedy...")
    resultado_greedy = ejecutar_greedy(df_top_k.copy())
 
    print(">> Ejecutando Weighted A*...")
    resultado_wastar = ejecutar_wastar(df_top_k.copy())
 
    tabla = pd.DataFrame([resultado_greedy, resultado_wastar]).set_index("algoritmo")
 
    columnas_orden = [
        "tiempo_ejecucion_seg",
        "pacientes_seleccionados",
        "horas_usadas",
        "horas_restantes",
        "costo_total_agenda",
        "pacientes_agendados",
    ]
    tabla = tabla[columnas_orden]
 
    print("\n" + "=" * 70)
    print("TABLA COMPARATIVA")
    print("=" * 70)
    print(tabla.to_string())
 
    # Guardar resultados
    salida_csv = Path(__file__).resolve().parent / "tabla_comparativa.csv"
    salida_md = Path(__file__).resolve().parent / "tabla_comparativa.md"
    tabla.to_csv(salida_csv, encoding="utf-8-sig")
    with open(salida_md, "w", encoding="utf-8") as f:
        f.write(tabla.to_markdown())
 
    print(f"\nTabla guardada en:\n  {salida_csv}\n  {salida_md}")
 
 
if __name__ == "__main__":
    main()


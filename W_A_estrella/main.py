import json
import os
import sys
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from modelos import Paciente
from traductor import traducir_valor
from algoritmo import weighted_a_star
from config_modelo import PESOS, VARIABLES_DEPENDIENTES_TIEMPO, LAMBDA_POR_TIPO

# Derivar splits estático/dinámico desde la única fuente de verdad.
COLS_ESTATICAS = [k for k in PESOS if k not in VARIABLES_DEPENDIENTES_TIEMPO]
COLS_DINAMICAS = [k for k in PESOS if k in VARIABLES_DEPENDIENTES_TIEMPO]

PESOS_ESTATICOS = {k: PESOS[k] for k in COLS_ESTATICAS}
PESOS_DINAMICOS = {k: PESOS[k] for k in COLS_DINAMICAS}


def cargar_datos_simulados(ruta_json: str, top_k: int | None = None):
    """
    Carga los pacientes del JSON y los transforma en objetos Paciente.
    """
    pacientes_instanciados = []

    with open(ruta_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)

    if top_k is not None:
        datos = sorted(
            datos,
            key=lambda p: (
                p["grupo_prioridad"],
                -p["vulnerabilidad"],
                -p["score_dinamico"],
            )
        )[:top_k]

    for p in datos:
        tiempo_minutos = int(p["duracion_cirugia_horas"] * 60)

        vars_estaticas = {k: traducir_valor(k, p[k]) for k in COLS_ESTATICAS}
        vars_dinamicas = {k: traducir_valor(k, p[k]) for k in COLS_DINAMICAS}

        paciente_obj = Paciente(
            id_paciente=p["id_paciente"],
            tiempo_quirurgico=tiempo_minutos,
            vars_estaticas=vars_estaticas,
            vars_dinamicas=vars_dinamicas,
            tipo_diag=p["tipo_diagnostico"],
            dias_espera_base=p["dias_en_lista"],
            jclin_meses=p.get("Jclin_meses"),
        )

        pacientes_instanciados.append(paciente_obj)

    return pacientes_instanciados


def simular_semanas(pacientes, capacidad_quirofano_minutos, peso_w, top_k,
                     dias_postergacion, n_semanas, verbose=True):
    """
    Ejecuta wA* semana a semana: en cada semana arma la agenda con los
    pacientes disponibles, retira a los agendados de la lista, y avanza
    +dias_postergacion la espera de los que quedaron pendientes.

    `top_k` aquí se usa exclusivamente como `top_k_candidatos` dentro de
    `weighted_a_star`: acota cuántos pacientes se consideran como rama de
    expansión en cada nodo de búsqueda, pero el pool de `pendientes` real
    (potencialmente los 200) se mantiene completo entre semanas.

    Devuelve (historial, pendientes_finales, metricas), donde `metricas` es
    un diccionario comparable al que produce `simulacion.simular_semanas_df`
    para Greedy/FIFO (mismas 3 métricas pedidas: promedio de días de espera
    al agendar, pacientes vulnerables sin operar, y tiempo de cómputo).
    """
    pendientes = pacientes
    historial = []
    tiempos_semana = []
    total_agendados = 0
    suma_dias_al_agendar = 0.0

    for semana in range(1, n_semanas + 1):
        if not pendientes:
            if verbose:
                print(f"\nTodos los pacientes fueron agendados antes de la semana {semana}.")
            break

        if verbose:
            print(f"\n{'─'*55}")
            print(f"SEMANA {semana} | Pendientes al inicio: {len(pendientes)}")
            print(f"{'─'*55}")

        t0 = time.perf_counter()
        estado_final = weighted_a_star(
            pacientes_totales=pendientes,
            capacidad_quirurgica=capacidad_quirofano_minutos,
            w=peso_w,
            pesos_estaticos=PESOS_ESTATICOS,
            pesos_dinamicos=PESOS_DINAMICOS,
            tasas_lambda=LAMBDA_POR_TIPO,
            top_k_candidatos=top_k,
            dias_postergacion=dias_postergacion,
        )
        t1 = time.perf_counter()
        tiempos_semana.append(t1 - t0)

        if estado_final is None:
            if verbose:
                print(f"Semana {semana}: no se encontró solución. Deteniendo simulación.")
            break

        agenda_semana = estado_final.agenda_parcial
        agendados_ids = {p.id for p in agenda_semana}
        tiempo_usado = sum(p.tiempo_quirurgico for p in agenda_semana)
        total_agendados += len(agenda_semana)
        suma_dias_al_agendar += sum(p.dias_espera_base for p in agenda_semana)

        if verbose:
            print(f"Agendados esta semana: {len(agenda_semana)} "
                  f"({tiempo_usado}/{capacidad_quirofano_minutos} min de pabellón usados) "
                  f"| tiempo de cómputo: {t1 - t0:.3f}s")
            for i, paciente in enumerate(agenda_semana, 1):
                """dias_espera_base: días totales que lleva esperando el paciente (incluye
                tanto el histórico del dataset como las semanas que fue postergado).
                dias_pospuestos: cuánto de eso corresponde a postergaciones DENTRO de
                esta simulación (0 si fue agendado en la primera semana en que apareció)."""
                print(f"  {i:02d}. ID {paciente.id:03d} | Tipo: {paciente.tipo_diag} " f"| T. Qx: {paciente.tiempo_quirurgico} min "
                      f"| Días esperando: {paciente.dias_espera_base} " f"| Días extra evaluados: {paciente.dias_pospuestos}")

        # Retirar agendados y avanzar el reloj de los que quedan
        pendientes = [p for p in pendientes if p.id not in agendados_ids]
        for p in pendientes:
            p.dias_espera_base += dias_postergacion
            p.dias_pospuestos += dias_postergacion

        # Vulnerables que quedan EN COLA esta semana (mismo criterio vp(t)>=1
        # que se usa para la métrica final, pero evaluado semana a semana en
        # vez de una sola vez al término de la simulación).
        vulnerables_en_cola = len([
            p for p in pendientes
            if p.vulnerabilidad() is not None and p.vulnerabilidad() >= 1
        ])

        historial.append({
            "semana": semana,
            "agendados": len(agenda_semana),
            "tiempo_usado_min": tiempo_usado,
            "pendientes_restantes": len(pendientes),
            "vulnerables_en_cola": vulnerables_en_cola,
            "tiempo_seg": t1 - t0,
        })

    vulnerables_pendientes = [
        p for p in pendientes
        if p.vulnerabilidad() is not None and p.vulnerabilidad() >= 1
    ]

    metricas = {
        "algoritmo": "Weighted A*",
        "semanas_ejecutadas": len(historial),
        "pacientes_agendados": total_agendados,
        "pacientes_pendientes_final": len(pendientes),
        "promedio_dias_espera_al_agendar": (
            suma_dias_al_agendar / total_agendados if total_agendados else float("nan")
        ),
        "pacientes_vulnerables_sin_operar": len(vulnerables_pendientes),
        "tiempo_computo_total_seg": sum(tiempos_semana),
        "tiempo_computo_promedio_seg_por_semana": (
            sum(tiempos_semana) / len(tiempos_semana) if tiempos_semana else 0.0
        ),
    }

    return historial, pendientes, metricas


def main():
    print("Iniciando sistema de agenda wA*...")
    ruta_json = "../data/pacientes.json" if not os.path.exists("data/pacientes.json") else "data/pacientes.json"

    try:
        # Parámetros del experimento
        horas_pabellon = 8
        capacidad_quirofano_minutos = int(horas_pabellon * 60)
        peso_w = 2.0
        top_k_candidatos = 40      # acota la RAMA de búsqueda por nodo, no la población
        dias_postergacion = 7
        n_semanas = 60             # tope de seguridad; la simulación real de 200
                                    # pacientes termina bastante antes (~29 semanas)

        # top_k=None: cargamos LOS 200 PACIENTES REALES. El recorte a top_k_candidatos
        # ocurre semana a semana, dentro de weighted_a_star, sobre el pool de
        # pendientes vigente (ver docstring de cargar_datos_simulados).
        pacientes = cargar_datos_simulados(ruta_json, top_k=None)
        print(f"¡Éxito! Se han cargado {len(pacientes)} pacientes (población completa).\n")

        print(
            f"Parámetros: horas_pabellon={horas_pabellon}h "
            f"= {capacidad_quirofano_minutos} min | w={peso_w} | "
            f"top_k_candidatos={top_k_candidatos} | dias_postergacion={dias_postergacion} | "
            f"n_semanas(tope)={n_semanas}\n"
        )

        historial, pendientes_finales, metricas = simular_semanas(
            pacientes,
            capacidad_quirofano_minutos,
            peso_w,
            top_k_candidatos,
            dias_postergacion,
            n_semanas,
        )

        print("\n" + "=" * 55)
        print("RESUMEN DE LA SIMULACIÓN wA*")
        print("=" * 55)
        print(f"top_k_candidatos usado por nodo: {top_k_candidatos}")
        print(f"Capacidad usada: {capacidad_quirofano_minutos} min/semana")
        print(f"Semanas simuladas: {metricas['semanas_ejecutadas']}")
        print(f"Total pacientes agendados: {metricas['pacientes_agendados']}/{len(pacientes)}")
        print(f"Pacientes sin agendar al final: {metricas['pacientes_pendientes_final']}")
        print(f"Pacientes vulnerables (vp>=1) sin operar: {metricas['pacientes_vulnerables_sin_operar']}")
        print(f"Promedio de días de espera al momento de agendar: "
              f"{metricas['promedio_dias_espera_al_agendar']:.1f}")
        print(f"Tiempo de cómputo total: {metricas['tiempo_computo_total_seg']:.2f}s "
              f"({metricas['tiempo_computo_promedio_seg_por_semana']:.3f}s/semana en promedio)")
        print("=" * 55 + "\n")

    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo JSON en la ruta: {ruta_json}")
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la ejecución: {e}")

if __name__ == "__main__":
    main()
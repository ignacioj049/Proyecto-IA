import json
import os
import sys
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


def cargar_datos_simulados(ruta_json: str):
    pacientes_instanciados = []
    with open(ruta_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    for p in datos:
        tiempo_minutos = int(p["duracion_cirugia_horas"] * 60)
        vars_estaticas = {k: traducir_valor(k, p[k]) for k in COLS_ESTATICAS}
        vars_dinamicas = {k: traducir_valor(k, p[k]) for k in COLS_DINAMICAS}
        paciente_obj = Paciente(
            id_paciente=p["id_paciente"], tiempo_quirurgico=tiempo_minutos,
            vars_estaticas=vars_estaticas, vars_dinamicas=vars_dinamicas,
            tipo_diag=p["tipo_diagnostico"], dias_espera_base=p["dias_en_lista"]
        )
        pacientes_instanciados.append(paciente_obj)
    return pacientes_instanciados


def simular_semanas(pacientes, capacidad_quirofano_minutos, peso_w, top_k,
                     dias_postergacion, n_semanas):
    """
    Ejecuta wA* semana a semana: en cada semana arma la agenda con los
    pacientes disponibles, retira a los agendados de la lista, y avanza
    +dias_postergacion la espera de los que quedaron pendientes.
    """
    pendientes = pacientes
    historial = []

    for semana in range(1, n_semanas + 1):
        if not pendientes:
            print(f"\nTodos los pacientes fueron agendados antes de la semana {semana}.")
            break

        print(f"\n{'─'*55}")
        print(f"SEMANA {semana} | Pendientes al inicio: {len(pendientes)}")
        print(f"{'─'*55}")

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

        if estado_final is None:
            print(f"Semana {semana}: no se encontró solución. Deteniendo simulación.")
            break

        agenda_semana = estado_final.agenda_parcial
        agendados_ids = {p.id for p in agenda_semana}
        tiempo_usado = sum(p.tiempo_quirurgico for p in agenda_semana)

        print(f"Agendados esta semana: {len(agenda_semana)} "
              f"({tiempo_usado}/{capacidad_quirofano_minutos} min de pabellón usados)")
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

        historial.append({
            "semana": semana,
            "agendados": len(agenda_semana),
            "tiempo_usado_min": tiempo_usado,
            "pendientes_restantes": len(pendientes),
        })

    return historial, pendientes


def main():
    print("Iniciando sistema de agenda wA* (simulación semanal)...")
    ruta_json = "../data/pacientes.json" if not os.path.exists("data/pacientes.json") else "data/pacientes.json"

    try:
        pacientes = cargar_datos_simulados(ruta_json)
        print(f"¡Éxito! Se han cargado {len(pacientes)} pacientes.\n")

        # Parámetros del experimento
        horas_pabellon = 8
        dias_laborales_semana = 5
        capacidad_quirofano_minutos = int(horas_pabellon * 60 * dias_laborales_semana)  # 2400 min/semana
        peso_w = 2.0
        top_k = 40
        dias_postergacion = 7
        n_semanas = 5

        print(f"Parámetros: horas_pabellon={horas_pabellon}h x {dias_laborales_semana} días "
            f"= {capacidad_quirofano_minutos} min/semana | w={peso_w} | "
            f"top_k={top_k} | dias_postergacion={dias_postergacion} | "
            f"n_semanas={n_semanas}\n")

        historial, pendientes_finales = simular_semanas(
            pacientes, capacidad_quirofano_minutos, peso_w,
            top_k, dias_postergacion, n_semanas
        )

        # Resumen final
        print("\n" + "="*55)
        print("RESUMEN DE LA SIMULACIÓN wA*")
        print("="*55)
        total_agendados = sum(h["agendados"] for h in historial)
        print(f"Semanas simuladas: {len(historial)}")
        print(f"Total pacientes agendados: {total_agendados}/{len(pacientes)}")
        print(f"Pacientes sin agendar al final: {len(pendientes_finales)}")
        if pendientes_finales:
            dias_espera = [p.dias_espera_base for p in pendientes_finales]
            print(f"Días de espera de los no agendados — "
                  f"mín: {min(dias_espera)} | máx: {max(dias_espera)} | "
                  f"promedio: {sum(dias_espera)/len(dias_espera):.1f}")
        print("=" * 55 + "\n")

    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo JSON en la ruta: {ruta_json}")
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la ejecución: {e}")

if __name__ == "__main__":
    main()
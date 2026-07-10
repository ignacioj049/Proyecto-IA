import json
import os
from modelos import Paciente
from traductor import traducir_valor
from algoritmo import weighted_a_star

def cargar_datos_simulados(ruta_json: str):
    pacientes_instanciados = []
    with open(ruta_json, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    for p in datos:
        tiempo_minutos = int(p["duracion_cirugia_horas"] * 60)
        vars_estaticas = {k: traducir_valor(k, p[k]) for k in ["Jclin", "Tlist", "Dest", "Opat", "Diag", "Ncuid", "Rcuid", "Dtrab", "Acc", "Dtras", "Ccrit"]}
        vars_dinamicas = {k: traducir_valor(k, p[k]) for k in ["Sever", "Urg", "Tsuen", "Pmcx", "Com", "Lfam", "Hanor", "Olim", "Dolor"]}
        paciente_obj = Paciente(
            id_paciente=p["id_paciente"], tiempo_quirurgico=tiempo_minutos,
            vars_estaticas=vars_estaticas, vars_dinamicas=vars_dinamicas,
            tipo_diag=p["tipo_diagnostico"], dias_espera_base=p["dias_en_lista"]
        )
        pacientes_instanciados.append(paciente_obj)
    return pacientes_instanciados

def main():
    print("Iniciando sistema de agenda wA*...")
    ruta_json = "../data/pacientes.json" if not os.path.exists("data/pacientes.json") else "data/pacientes.json"
    
    try:
        # Cargar datos
        pacientes = cargar_datos_simulados(ruta_json)
        print(f"¡Éxito! Se han cargado {len(pacientes)} pacientes.\n")
        
        # Definir parámetros del quirófano 
        capacidad_quirofano_minutos = 2400 
        
        # Definir el peso de relajación (w) para el wA*
        peso_w = 2.0 
        
        print(f"Calculando agenda óptima para {capacidad_quirofano_minutos} minutos con w={peso_w}...")
        
        pesos_estaticos = {"Jclin": 1.0, "Tlist": 0.5, "Opat": 0.8} 
        pesos_dinamicos = {"Sever": 1.2, "Urg": 1.5, "Dolor": 1.1}  
        tasas_lambda = {"Sever": 0.05, "Urg": 0.1, "Dolor": 0.02}   
        
        # Ejecutamos la búsqueda pasando todos los parámetros requeridos
        estado_final = weighted_a_star(
            pacientes_totales=pacientes, 
            capacidad_quirurgica=capacidad_quirofano_minutos, 
            w=peso_w,
            pesos_estaticos=pesos_estaticos,
            pesos_dinamicos=pesos_dinamicos,
            tasas_lambda=tasas_lambda
        )
        
        if estado_final is None:
            print("No se encontró una solución válida que cumpla las restricciones.")
            return

        # 5. Imprimir los resultados en consola
        print("\n" + "="*55)
        print("🏥 ORDEN DE PACIENTES SUGERIDO POR wA* 🏥")
        print("="*55)
        
        tiempo_usado = 0
        
        # Extraemos la lista de pacientes del EstadoNodo devuelto
        agenda_optima = estado_final.agenda_parcial 
        
        for i, paciente in enumerate(agenda_optima, 1):
            tiempo_usado += paciente.tiempo_quirurgico
            print(f"{i:02d}. Paciente ID: {paciente.id:03d} | Tipo: {paciente.tipo_diag} | T. Qx: {paciente.tiempo_quirurgico} min | T. Acumulado: {tiempo_usado} min")
            
        print("-" * 55)
        print(f"Resumen: Se programaron {len(agenda_optima)} pacientes en la agenda.")
        print(f"Tiempo total de quirófano utilizado: {tiempo_usado}/{capacidad_quirofano_minutos} minutos.")
        print("=" * 55 + "\n")
        
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo JSON en la ruta: {ruta_json}")
    except Exception as e:
        print(f"Ocurrió un error inesperado durante la ejecución: {e}")

if __name__ == "__main__":
    main()
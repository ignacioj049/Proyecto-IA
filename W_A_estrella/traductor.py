# traductor.py

"""
Módulo de traducción para convertir variables categóricas (texto) 
a valores numéricos (pesos alpha) según el paper de referencia.
"""

MAPEO_VALORES = {
    # VARIABLES ESTÁTICAS 
    "Jclin": {
        "I": 1.0, "II": 2.0, "III": 3.0, "IV": 4.0, "V": 5.0, 
        "VI": 6.0, "VII": 7.0, "VIII": 8.0, "IX": 9.0, "X": 10.0
    }, 
    "Tlist": {
        "0-3": 0.1, "4-6": 0.5, "7-9": 0.9, "10-12": 1.2, "13-18": 1.5, "+10": 1.0
    },
    "Dest": {"sí": 1.0, "no": 0.0, "NA": 0.0},
    "Opat": {
        "0": 0.0, "1": 1.0, "2": 2.0, "3": 3.0,
        "I": 1.0, "II": 2.0, "III": 3.0, "IV": 4.0
    }, 
    "Diag": {
        # Diagnósticos originales
        "Desviación septal sin apnea": 0.3, 
        "Amigdalitis crónica o recurrente": 0.6, 
        "Hipertrofia de amígdalas y adenoides": 0.8,
        # Diagnósticos capturados de tu consola
        "Obstrucción de conductos lagrimales": 0.4,
        "Obstrucción lacrimal": 0.4,
        "Colesteatoma del oído": 0.9,
        "Perforación timpánica": 0.5,
        "Septoplastia con apnea": 0.7,
        "Sinusitis crónica complicada": 0.8,
        "Sinusitis crónica simple": 0.3,
        "Otitis media complicada": 0.8,
        "Otitis media con efusión": 0.4,
        "Pólipo nasal con apnea": 0.7,
        "Pólipo nasal sin apnea": 0.4,
        "Amígdalas obstructivas con apnea": 0.9,
        "Mucocele frontal": 0.6,
        "Rinodesviación": 0.3
    },
    "Ncuid": {"sí": 1.0, "no": 0.0},
    "Rcuid": {"sí": 1.0, "no": 0.0},
    "Dtrab": {"sí": 1.0, "no": 0.0, "NA": 0.0},
    "Acc": {
        "urbano": 0.3, 
        "rural": 0.7, 
        "alta ruralidad": 1.0
    },
    "Dtras": {"sí": 1.0, "no": 0.0},
    "Ccrit": {"sí": 1.0, "no": 0.0},
    
    # VARIABLES DINÁMICAS 
    "Sever": {"alta": 1.0, "media": 0.6, "baja": 0.2},
    "Tsuen": {"severo": 1.0, "medio": 0.6, "bajo": 0.2},
    "Pmcx": {"alta": 1.0, "media": 0.6, "baja": 0.2},
    "Com": {"alta": 1.0, "media": 0.5, "baja": 0.1},
    "Lfam": {"sí": 1.0, "no": 0.0},
    "Hanor": {"alta presencia": 1.0, "baja presencia": 0.3, "sin presencia": 0.0},
    "Olim": {"severa": 1.0, "media": 0.6, "no": 0.0}
}

def traducir_valor(variable: str, valor):
    
    #Convierte el texto del JSON al valor numérico correspondiente para los cálculos.
    
    if isinstance(valor, (int, float)):
        return float(valor)
    
    if variable in MAPEO_VALORES and valor in MAPEO_VALORES[variable]:
        return MAPEO_VALORES[variable][valor]
        
    print(f"  [!] Advertencia: Valor '{valor}' no encontrado para la variable '{variable}'. Asignando 0.0")
    return 0.0
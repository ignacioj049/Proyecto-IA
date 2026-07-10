"""
Módulo de traducción para convertir variables categóricas (texto) 
a valores numéricos (pesos alpha) según el paper de referencia.
"""
MAPEO_VALORES = {
    # VARIABLES ESTÁTICAS 
    "Jclin": {
        "I": 0.197, "II": 0.175, "III": 0.149, "IV": 0.121, "V": 0.090, 
        "VI": 0.079, "VII": 0.062, "VIII": 0.054, "IX": 0.045, "X": 0.028
    }, 
    "Tlist": {
        "0-3": 0.036, "4-6": 0.052, "7-9": 0.072, "10-12": 0.092, 
        "13-18": 0.106, "19-24": 0.112, "25-36": 0.121, "37-48": 0.128, 
        "49-60": 0.137, "+60": 0.144
    },
    "Dest": {"NA": 0.0, "sí": 0.940, "no": 0.060},
    "Opat": {
        "0": 0.068, "I": 0.151, "1": 0.151, "II": 0.212, "2": 0.212, 
        "III": 0.253, "3": 0.253, "IV": 0.315, "4": 0.315, "+3": 0.315
    }, 
    "Diag": {
        "Hipertrofia de amígdalas y adenoides": 0.051,
        "Amigdalitis crónica o recurrente": 0.046,
        "Obstrucción de conductos lagrimales": 0.061,
        "Obstrucción lacrimal": 0.061,
        "Colesteatoma del oído": 0.070,
        "Perforación timpánica": 0.045,
        "Septoplastia con apnea": 0.060,
        "Sinusitis crónica complicada": 0.070,
        "Sinusitis crónica simple": 0.052,
        "Otitis media complicada": 0.076,
        "Otitis media con efusión": 0.064,
        "Pólipo nasal con apnea": 0.062,
        "Pólipo nasal sin apnea": 0.044,
        "Amígdalas obstructivas con apnea": 0.065,
        "Mucocele frontal": 0.060,
        "Rinodesviación": 0.035,
        "Desviación septal sin apnea": 0.038
    },
    "Ncuid": {"sí": 0.932, "no": 0.068},
    "Rcuid": {"sí": 0.939, "no": 0.061},
    "Dtrab": {"NA": 0.0, "sí": 0.929, "no": 0.071},
    "Acc": {"urbano": 0.104, "rural": 0.343, "alta ruralidad": 0.552},
    "Dtras": {"sí": 0.875, "no": 0.125},
    "Ccrit": {"sí": 0.652, "no": 0.348},
    
    # VARIABLES DINÁMICAS 
    "Sever": {"alta": 0.650, "media": 0.290, "baja": 0.060},
    "Urg": {
        "0": 0.0, "1": 0.016, "2": 0.029, "3": 0.043, "4": 0.067, 
        "5": 0.094, "6": 0.110, "7": 0.126, "8": 0.155, "9": 0.172, "10": 0.188
    },
    "Tsuen": {"severo": 0.660, "medio": 0.290, "bajo": 0.050},
    "Pmcx": {"alta": 0.625, "media": 0.330, "baja": 0.045},
    "Com": {"alta": 0.598, "media": 0.353, "baja": 0.049},
    "Lfam": {"sí": 0.909, "no": 0.091},
    "Hanor": {"alta presencia": 0.611, "baja presencia": 0.333, "sin presencia": 0.056},
    "Olim": {"severa": 0.612, "media": 0.340, "no": 0.049},
    "Dolor": {
        "0": 0.0, "1": 0.016, "2": 0.032, "3": 0.045, "4": 0.080, 
        "5": 0.096, "6": 0.110, "7": 0.128, "8": 0.147, "9": 0.166, "10": 0.179
    }
}

def traducir_valor(variable: str, valor):
    
    #Convierte el texto del JSON al valor numérico correspondiente para los cálculos.
    
    if isinstance(valor, (int, float)):
        return float(valor)
    
    if variable in MAPEO_VALORES and valor in MAPEO_VALORES[variable]:
        return MAPEO_VALORES[variable][valor]
        
    print(f"  [!] Advertencia: Valor '{valor}' no encontrado para la variable '{variable}'. Asignando 0.0")
    return 0.0
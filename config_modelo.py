"""
================================================================================
 CONFIG_MODELO — Parámetros comunes del modelo matemático del paper
================================================================================
Basado en el paper:
  Silva-Aravena, F., Álvarez-Miranda, E., Astudillo, C.A., González-Martínez, L.,
  Ledezma, J.G. (2021). "Patients' Prioritization on Surgical Waiting Lists:
  A Decision Support System". Mathematics, 9(10), 1097.
  https://doi.org/10.3390/math9101097

Este módulo centraliza TODOS los parámetros del modelo para que todo el equipo
(Persona 1: generación de datos, Persona 2: Weighted A*, Persona 3: comparación
de enfoques) use exactamente los mismos pesos, alphas, lambdas y funciones de
score. No debe haber una segunda copia de estas constantes en otro archivo.
================================================================================
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. PESOS wi — Tabla 4 del paper (calibrados por 7 médicos, suman 1.0)
# ─────────────────────────────────────────────────────────────────────────────
PESOS = {
    "Sever": 0.081,  # Gravedad/progresión de la enfermedad        (*)
    "Urg":   0.076,  # Urgencia clínica                            (*)
    "Jclin": 0.066,  # Tiempo máximo de espera según criterio médico
    "Tsuen": 0.063,  # Trastorno del sueño                         (*)
    "Tlist": 0.062,  # Tiempo en lista de espera
    "Pmcx":  0.055,  # Probabilidad de mejora con la cirugía       (*)
    "Dest":  0.054,  # Capacidad de estudio                        (*)
    "Com":   0.053,  # Probabilidad de desarrollar comorbilidades  (*)
    "Lfam":  0.053,  # Capacidad de actividades familiares         (*)
    "Hanor": 0.052,  # Área anatómica afectada                     (*)
    "Opat":  0.047,  # Otras patologías presentes
    "Diag":  0.046,  # Diagnóstico de ingreso a la lista
    "Olim":  0.045,  # Otras limitaciones funcionales              (*)
    "Ncuid": 0.043,  # Necesita un cuidador
    "Rcuid": 0.043,  # Es responsable de cuidar a otra persona
    "Dolor": 0.040,  # Escala de dolor (EVA)                       (*)
    "Dtrab": 0.038,  # Capacidad laboral
    "Acc":   0.033,  # Tipo de residencia / ruralidad
    "Dtras": 0.028,  # Dificultad de traslado al hospital
    "Ccrit": 0.023,  # Necesita cama crítica
}

# (*) = variable dependiente del tiempo (Tabla 4 del paper, marcadas con asterisco)
VARIABLES_DEPENDIENTES_TIEMPO = {
    "Sever", "Urg", "Tsuen", "Pmcx", "Dest",
    "Com", "Lfam", "Hanor", "Olim", "Dolor"
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. VALORES α POR CATEGORÍA — Apéndice B del paper (traducidos al español)
# ─────────────────────────────────────────────────────────────────────────────
ALPHA = {
    "Sever": {"baja": 0.06, "media": 0.29, "alta": 0.65},

    # Urg y Dolor usan la tabla alpha del paper (Apéndice B, puntos 2 y 16),
    # NO un cálculo directo a partir del valor numérico crudo.
    "Urg": {0: 0.000, 1: 0.016, 2: 0.029, 3: 0.043, 4: 0.067, 5: 0.094,
            6: 0.110, 7: 0.126, 8: 0.155, 9: 0.172, 10: 0.188},

    # Jclin: tiempo máximo recomendado por el médico, en categorías (meses)
    "Jclin": {"I": 0.197, "II": 0.175, "III": 0.149, "IV": 0.121, "V": 0.090,
              "VI": 0.079, "VII": 0.062, "VIII": 0.054, "IX": 0.045, "X": 0.028},

    "Tsuen": {"bajo": 0.05, "medio": 0.29, "severo": 0.66},

    "Tlist": {"0-3": 0.036, "4-6": 0.052, "7-9": 0.072, "10-12": 0.092,
              "13-18": 0.106, "19-24": 0.112, "25-36": 0.121,
              "37-48": 0.128, "49-60": 0.137, "+60": 0.144},

    "Pmcx": {"baja": 0.045, "media": 0.330, "alta": 0.625},
    "Dest": {"NA": 0.0, "sí": 0.94, "no": 0.06},
    "Com":  {"baja": 0.049, "media": 0.353, "alta": 0.598},
    "Lfam": {"sí": 0.909, "no": 0.091},

    "Hanor": {"sin presencia": 0.056, "baja presencia": 0.333, "alta presencia": 0.611},
    "Opat":  {"0": 0.068, "I": 0.151, "II": 0.212, "III": 0.253, "IV": 0.315},

    # 18 diagnósticos ORL — Tabla 2 del paper (traducidos)
    "Diag": {
        "Otitis media complicada":              0.076,
        "Colesteatoma del oído":                0.070,
        "Sinusitis crónica complicada":         0.070,
        "Amígdalas obstructivas con apnea":     0.065,
        "Otitis media con efusión":             0.064,
        "Pólipo nasal con apnea":               0.062,
        "Apnea obstructiva del sueño":          0.061,  
        "Obstrucción lacrimal":                 0.061,
        "Mucocele frontal":                     0.060,
        "Septoplastia con apnea":               0.060,
        "Sinusitis crónica simple":             0.052,
        "Hipertrofia de amígdalas y adenoides": 0.051,
        "Amigdalitis crónica o recurrente":     0.046,
        "Perforación timpánica":                0.045,
        "Pólipo nasal sin apnea":               0.044,
        "Obstrucción de conductos lagrimales":  0.041, 
        "Desviación septal sin apnea":          0.038,
        "Rinodesviación":                       0.035,
    },

    "Olim":  {"no": 0.049, "media": 0.340, "severa": 0.612},
    "Ncuid": {"sí": 0.932, "no": 0.068},
    "Rcuid": {"sí": 0.939, "no": 0.061},

    "Dolor": {0: 0.000, 1: 0.016, 2: 0.032, 3: 0.045, 4: 0.080, 5: 0.096,
              6: 0.110, 7: 0.128, 8: 0.147, 9: 0.166, 10: 0.179},

    "Dtrab": {"NA": 0.0, "sí": 0.929, "no": 0.071},
    "Acc":   {"urbano": 0.104, "rural": 0.343, "alta ruralidad": 0.552},
    "Dtras": {"sí": 0.875, "no": 0.125},
    "Ccrit": {"sí": 0.652, "no": 0.348},
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. CLASIFICACIÓN DE DIAGNÓSTICOS EN TIPO A / B / C — Sección 3.5 del paper
#    A = empeora rápido | B = rápido al inicio, luego estable | C = lento
#    (El paper solo da 3 ejemplos explícitos; el resto es extrapolación nuestra)
# ─────────────────────────────────────────────────────────────────────────────
TIPO_DIAGNOSTICO = {
    "Hipertrofia de amígdalas y adenoides": "A",  
    "Amígdalas obstructivas con apnea":     "A",
    "Apnea obstructiva del sueño":          "A",
    "Pólipo nasal con apnea":               "A",
    "Septoplastia con apnea":               "A",
    "Colesteatoma del oído":                "B", 
    "Otitis media complicada":              "B",
    "Sinusitis crónica complicada":         "B",
    "Mucocele frontal":                     "B",
    "Otitis media con efusión":             "B",
    "Obstrucción lacrimal":                 "B",
    "Amigdalitis crónica o recurrente":     "C", 
    "Perforación timpánica":                "C",
    "Sinusitis crónica simple":             "C",
    "Pólipo nasal sin apnea":               "C",
    "Obstrucción de conductos lagrimales":  "C",
    "Desviación septal sin apnea":          "C",
    "Rinodesviación":                       "C",
}

# Factores de empeoramiento λ por tipo de diagnóstico, para los 4 intervalos
# h=1 (0-90d), h=2 (90-180d), h=3 (180-360d), h=4 (360-540d).
# Calibrados para acercarse a los anclas del paper:
#   Tipo A (hipertrofia): ~1.6x acumulado a los 90 días
#   Tipo C (amigdalitis): ~1.2x acumulado a los 90 días
LAMBDA_POR_TIPO = {
    "A": [0.55, 0.25, 0.20, 0.15],
    "B": [0.30, 0.15, 0.05, 0.05],
    "C": [0.18, 0.08, 0.06, 0.04],
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. EXTENSIÓN PROPIA (NO viene del paper): duración de cirugía por diagnóstico
#    Necesaria para el Weighted A* del proyecto (capacidad de pabellón/slots),
#    ya que el paper no modela tiempos quirúrgicos.
# ─────────────────────────────────────────────────────────────────────────────
DURACION_CIRUGIA_HORAS = {
    "Hipertrofia de amígdalas y adenoides": 1.0,
    "Amígdalas obstructivas con apnea":     1.2,
    "Amigdalitis crónica o recurrente":     0.8,
    "Otitis media complicada":              1.5,
    "Colesteatoma del oído":                2.5,
    "Perforación timpánica":                1.0,
    "Sinusitis crónica complicada":         2.0,
    "Sinusitis crónica simple":             1.3,
    "Desviación septal sin apnea":          1.2,
    "Rinodesviación":                       1.2,
    "Septoplastia con apnea":               1.5,
    "Pólipo nasal con apnea":               1.3,
    "Pólipo nasal sin apnea":               1.0,
    "Obstrucción lacrimal":                 0.7,
    "Obstrucción de conductos lagrimales":  0.7,
    "Mucocele frontal":                     1.8,
    "Otitis media con efusión":             0.6,
    "Apnea obstructiva del sueño":          1.4,
}

"""
================================================================================
 GENERADOR DE DATASET SINTÉTICO DE PACIENTES — LISTA DE ESPERA QUIRÚRGICA
================================================================================
Basado en el paper:
  Silva-Aravena, F., Álvarez-Miranda, E., Astudillo, C.A., González-Martínez, L.,
  Ledezma, J.G. (2021). "Patients' Prioritization on Surgical Waiting Lists:
  A Decision Support System". Mathematics, 9(10), 1097.
  https://doi.org/10.3390/math9101097

Contexto real del paper: Unidad de Otorrinolaringología (ORL),
Hospital de Talca, Chile (2018-2019).

Este script reproduce fielmente:
  - Las 20 variables biopsicosociales (Tabla 4 del paper)
  - Los pesos wi calibrados por 7 médicos (Tabla 4)
  - Los valores alpha de cada categoría (Apéndice B)
  - El score estático sp (Ecuación 3)
  - El score dinámico s'p(t) con deterioro temporal (Sección 3.4.2)
  - La función de vulnerabilidad vp(t) (Ecuación 4)
  - La clasificación en 4 grupos de prioridad (Sección 3.5)

Nota de transparencia: el paper NO publica la tabla completa de factores de
empeoramiento λ para las 18 diagnósticos x 10 variables dependientes del
tiempo (esa calibración fue interna del equipo médico de Talca). El paper
solo da un ejemplo explícito (variable Urg, diagnóstico "hipertrofia de
amígdalas y adenoides": 10%, 20%, 30%, 40% de empeoramiento por intervalo) y
dos resultados agregados (Fig. 1: hipertrofia llega a un factor ~1.6x a los
90 días; amigdalitis crónica llega a ~1.2x). Usamos esos datos como anclas
y extrapolamos razonablemente para el resto de diagnósticos, clasificándolos
en Tipo A (empeoran rápido), B (rápido al inicio, luego estable) y C (lento),
tal como describe la Sección 3.5 del paper.
================================================================================
"""

import numpy as np
import pandas as pd
import os

from config_modelo import (
    PESOS,
    VARIABLES_DEPENDIENTES_TIEMPO,
    ALPHA,
    TIPO_DIAGNOSTICO,
    LAMBDA_POR_TIPO,
    DURACION_CIRUGIA_HORAS,
)
from scoring import score_estatico, score_dinamico, vulnerabilidad

# NOTA: PESOS, ALPHA, VARIABLES_DEPENDIENTES_TIEMPO, TIPO_DIAGNOSTICO,
# LAMBDA_POR_TIPO y DURACION_CIRUGIA_HORAS ahora viven en config_modelo.py,
# y score_estatico/score_dinamico/vulnerabilidad viven en scoring.py, para
# que todo el equipo (generación de datos, Greedy, Weighted A*, comparación
# de enfoques) use exactamente los mismos parámetros y la misma función de
# riesgo.

# Distribución real de diagnósticos — Tabla 2 del paper (205 pacientes reales)
CONTEO_DIAGNOSTICOS = {
    "Hipertrofia de amígdalas y adenoides": 78,
    "Amigdalitis crónica o recurrente":     31,
    "Perforación timpánica":                21,
    "Desviación septal sin apnea":          17,
    "Amígdalas obstructivas con apnea":     13,
    "Otitis media complicada":              10,
    "Obstrucción de conductos lagrimales":   7,
    "Colesteatoma del oído":                 6,
    "Pólipo nasal sin apnea":                4,
    "Sinusitis crónica complicada":          4,
    "Rinodesviación":                        4,
    "Pólipo nasal con apnea":                3,
    "Obstrucción lacrimal":                  3,
    "Otitis media con efusión":              1,
    "Mucocele frontal":                      1,
    "Septoplastia con apnea":                1,
    "Sinusitis crónica simple":              1,
    "Apnea obstructiva del sueño":           1,  # el paper reporta 0; usamos 1
}

# ─────────────────────────────────────────────────────────────────────────────
# 5. FUNCIONES AUXILIARES DE CATEGORIZACIÓN
# ─────────────────────────────────────────────────────────────────────────────

def categoria_tlist(dias_en_lista):
    """Convierte días en lista a categoría Tlist del paper (en meses)."""
    meses = dias_en_lista / 30.44
    bordes = [3, 6, 9, 12, 18, 24, 36, 48, 60]
    etiquetas = ["0-3", "4-6", "7-9", "10-12", "13-18",
                 "19-24", "25-36", "37-48", "49-60", "+60"]
    for borde, etiqueta in zip(bordes, etiquetas):
        if meses <= borde:
            return etiqueta
    return "+60"


def categoria_jclin(espera_max_meses):
    """Convierte tiempo máximo recomendado (meses) a categoría Jclin (I a X)."""
    bordes = [3, 6, 9, 12, 18, 24, 36, 48, 60]
    etiquetas = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    for borde, etiqueta in zip(bordes, etiquetas):
        if espera_max_meses <= borde:
            return etiqueta
    return "X"


def distribucion_edades():
    """
    Distribución de edad según Tabla 1 del paper:
    0-20: 126/205, 21-40: 25/205, 41-60: 32/205, +60: 22/205
    """
    edades, probs = [], []
    rangos = [(0, 20, 126), (21, 40, 25), (41, 60, 32), (61, 100, 22)]
    for ini, fin, n in rangos:
        ancho = fin - ini + 1
        for e in range(ini, fin + 1):
            edades.append(e)
            probs.append(n / 205 / ancho)
    total = sum(probs)
    return edades, [p / total for p in probs]


def probabilidades_diagnostico():
    """Distribución de diagnósticos según Tabla 2 del paper."""
    total = sum(CONTEO_DIAGNOSTICOS.values())
    diags = list(CONTEO_DIAGNOSTICOS.keys())
    probs = [v / total for v in CONTEO_DIAGNOSTICOS.values()]
    return diags, probs


# ─────────────────────────────────────────────────────────────────────────────
# 6. MODELO MATEMÁTICO DEL PAPER: SCORE Y VULNERABILIDAD
#    (implementación única en scoring.py, usada también por Greedy y wA*)
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# 7. GENERADOR PRINCIPAL DEL DATASET
# ─────────────────────────────────────────────────────────────────────────────

def generar_pacientes(n: int = 200, semilla: int = 42) -> pd.DataFrame:
    """
    Genera n pacientes sintéticos con las 20 variables biopsicosociales
    del paper. Las proporciones demográficas y de diagnóstico respetan
    los datos reales reportados (Tabla 1 y Tabla 2: 205 pacientes de la
    unidad de ORL, Hospital de Talca, 2018).

    Las variables clínicas individuales (Sever, Urg, Dolor, etc.) NO tienen
    distribución poblacional publicada en el paper —son evaluaciones caso
    a caso del médico tratante—, por lo que aquí se generan con distribuciones
    plausibles y documentadas, pensadas para producir una lista de espera
    realista y con suficiente variabilidad para el proyecto.

    Retorna
    -------
    pd.DataFrame con las 20 variables, los scores y la vulnerabilidad
    de cada paciente, listo para alimentar el algoritmo Weighted A*.
    """
    rng = np.random.default_rng(semilla)
    edades_vals, edades_probs = distribucion_edades()
    diag_nombres, diag_probs = probabilidades_diagnostico()

    filas = []
    for pid in range(1, n + 1):

        # ── Información general ──────────────────────────────────────────
        edad = int(rng.choice(edades_vals, p=edades_probs))
        genero = rng.choice(["M", "F"], p=[0.45, 0.55])
        tipo_paciente = rng.choice(["nuevo", "en tratamiento"], p=[38/205, 167/205])

        # ── Diagnóstico (Tabla 2 real) ───────────────────────────────────
        diagnostico = rng.choice(diag_nombres, p=diag_probs)

        # ── Tiempo en lista (días); el paper opera hasta 540 días ───────
        dias_en_lista = int(np.clip(rng.exponential(120), 7, 540))

        # ── VARIABLES CLÍNICAS ────────────────────────────────────────────
        Sever = rng.choice(["baja", "media", "alta"], p=[0.15, 0.45, 0.40])
        Urg = int(rng.choice(range(11),
                  p=[0.02,0.03,0.06,0.08,0.10,0.15,0.18,0.16,0.12,0.06,0.04]))
        Jclin_meses = int(rng.choice(
            [2, 5, 8, 11, 15, 21, 30, 42, 54, 72],
            p=[0.20,0.20,0.15,0.12,0.10,0.08,0.07,0.04,0.02,0.02]))
        Jclin = categoria_jclin(Jclin_meses)
        Tsuen = rng.choice(["bajo", "medio", "severo"], p=[0.40, 0.40, 0.20])
        Pmcx  = rng.choice(["baja", "media", "alta"], p=[0.10, 0.35, 0.55])
        Com   = rng.choice(["baja", "media", "alta"], p=[0.30, 0.45, 0.25])
        Hanor = rng.choice(["sin presencia", "baja presencia", "alta presencia"],
                            p=[0.30, 0.45, 0.25])
        n_opat = rng.choice([0, 1, 2, 3, 4], p=[150/205, 38/205, 13/205, 3/205, 1/205])
        Opat  = ["0", "I", "II", "III", "IV"][n_opat]
        Olim  = rng.choice(["no", "media", "severa"], p=[0.20, 0.50, 0.30])
        Dolor = int(rng.choice(range(11),
                    p=[0.03,0.04,0.06,0.08,0.10,0.14,0.18,0.16,0.12,0.06,0.03]))
        Ccrit = rng.choice(["sí", "no"], p=[0.05, 0.95])

        # ── VARIABLES PSICOSOCIALES ───────────────────────────────────────
        Tlist = categoria_tlist(dias_en_lista)
        Dest  = (rng.choice(["sí", "no", "NA"], p=[0.50, 0.30, 0.20]) if edad < 25
                 else rng.choice(["sí", "no", "NA"], p=[0.05, 0.10, 0.85]))
        Lfam  = rng.choice(["sí", "no"], p=[0.55, 0.45])
        Ncuid = rng.choice(["sí", "no"], p=[0.20, 0.80])
        Rcuid = rng.choice(["sí", "no"], p=[0.35, 0.65])
        Dtrab = ("NA" if (edad < 18 or edad > 65)
                  else rng.choice(["sí", "no", "NA"], p=[0.50, 0.35, 0.15]))
        Acc   = rng.choice(["urbano", "rural", "alta ruralidad"], p=[0.55, 0.30, 0.15])
        Dtras = rng.choice(["sí", "no"], p=[0.20, 0.80])

        paciente = {
            "id_paciente": pid, "edad": edad, "genero": genero,
            "tipo_paciente": tipo_paciente, "dias_en_lista": dias_en_lista,
            "Jclin_meses": Jclin_meses,
            "Sever": Sever, "Urg": Urg, "Jclin": Jclin, "Tsuen": Tsuen,
            "Tlist": Tlist, "Pmcx": Pmcx, "Dest": Dest, "Com": Com,
            "Lfam": Lfam, "Hanor": Hanor, "Opat": Opat, "Diag": diagnostico,
            "Olim": Olim, "Ncuid": Ncuid, "Rcuid": Rcuid, "Dolor": Dolor,
            "Dtrab": Dtrab, "Acc": Acc, "Dtras": Dtras, "Ccrit": Ccrit,
            "tipo_diagnostico": TIPO_DIAGNOSTICO[diagnostico],
            # Extensión propia para el Weighted A* (no viene del paper):
            "duracion_cirugia_horas": DURACION_CIRUGIA_HORAS[diagnostico],
        }

        paciente["score_estatico"] = round(score_estatico(paciente), 4)
        paciente["score_dinamico"] = round(score_dinamico(paciente, 0), 4)
        paciente["vulnerabilidad"] = round(vulnerabilidad(paciente, 0), 4)

        filas.append(paciente)

    df = pd.DataFrame(filas)

    # ── Clasificación en 4 grupos de prioridad — Sección 3.5 del paper ───────
    promedio_score = df["score_dinamico"].mean()

    def clasificar(fila):
        alto = fila["score_dinamico"] >= promedio_score
        vulnerable = fila["vulnerabilidad"] >= 1
        if alto and vulnerable:     return 1  # máxima prioridad
        if alto and not vulnerable: return 2
        if not alto and vulnerable: return 3
        return 4                                # mínima prioridad

    df["grupo_prioridad"] = df.apply(clasificar, axis=1)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# 8. VALIDACIÓN CONTRA EL EJEMPLO DEL PAPER (Tabla 5, Sección 3.4.2)
# ─────────────────────────────────────────────────────────────────────────────

def validar_contra_ejemplo_paper():
    """
    Reproduce el ejemplo artificial de la Sección 3.4.2 del paper:
    paciente de 10 años, diagnóstico "amigdalitis crónica o recurrente",
    Urg=6, ingresado el 31.08.2018, para comparar sp y vp(t) contra la
    Tabla 5 del paper.
    """
    paciente_ejemplo = {
        "Sever": "media", "Urg": 5, "Jclin": "VIII", "Tsuen": "medio",
        "Tlist": "0-3", "Pmcx": "alta", "Dest": "NA", "Com": "media",
        "Lfam": "no", "Hanor": "baja presencia", "Opat": "0",
        "Diag": "Amigdalitis crónica o recurrente", "Olim": "media",
        "Ncuid": "sí", "Rcuid": "no", "Dolor": 6, "Dtrab": "NA",
        "Acc": "urbano", "Dtras": "no", "Ccrit": "no",
        "Jclin_meses": 9,        # categoría VIII ≈ 9 meses
        "dias_en_lista": 0,
    }

    print("\n" + "=" * 65)
    print("  VALIDACIÓN CONTRA EL EJEMPLO DEL PAPER (Tabla 5, Sección 3.4.2)")
    print("=" * 65)
    print(f"\n  Paper reporta: sp(t=0) = 3.830 (escala 0-100, distinta normalización)")
    print(f"  Nuestro score_estatico (escala 0-1): "
          f"{score_estatico(paciente_ejemplo):.4f}")
    print(f"  (la escala difiere porque el paper multiplica por 100 en su reporte;")
    print(f"   lo importante es que el ORDEN RELATIVO entre pacientes se preserva)")
    print()
    for dias in [0, 90, 180, 270, 365]:
        s = score_dinamico(paciente_ejemplo, dias)
        v = vulnerabilidad(paciente_ejemplo, dias)
        print(f"  t = {dias:>4} días  ->  score_dinamico = {s:.4f}   "
              f"vulnerabilidad = {v:.3f}")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 9. RESUMEN DESCRIPTIVO
# ─────────────────────────────────────────────────────────────────────────────

def imprimir_resumen(df: pd.DataFrame) -> None:
    print("=" * 65)
    print(f"  DATASET GENERADO: {len(df)} pacientes")
    print("=" * 65)

    print(f"\nScore estático   — media: {df['score_estatico'].mean():.4f}  "
          f"mín: {df['score_estatico'].min():.4f}  máx: {df['score_estatico'].max():.4f}")
    print(f"Score dinámico   — media: {df['score_dinamico'].mean():.4f}  "
          f"mín: {df['score_dinamico'].min():.4f}  máx: {df['score_dinamico'].max():.4f}")
    print(f"Vulnerabilidad   — media: {df['vulnerabilidad'].mean():.4f}  "
          f"mín: {df['vulnerabilidad'].min():.4f}  máx: {df['vulnerabilidad'].max():.4f}")
    print(f"Días en lista    — media: {df['dias_en_lista'].mean():.1f}  "
          f"mín: {df['dias_en_lista'].min()}  máx: {df['dias_en_lista'].max()}")

    print(f"\nGrupos de prioridad (Sección 3.5 del paper):")
    etiquetas = {1: "Alto score + Vulnerable  (prioridad máxima)",
                 2: "Alto score + No vulnerable",
                 3: "Bajo score + Vulnerable",
                 4: "Bajo score + No vulnerable (prioridad mínima)"}
    for g in [1, 2, 3, 4]:
        n = (df["grupo_prioridad"] == g).sum()
        print(f"  Grupo {g} ({etiquetas[g]}): {n} pacientes ({n/len(df)*100:.1f}%)")

    print(f"\nTipo de diagnóstico (velocidad de deterioro):")
    for t in ["A", "B", "C"]:
        n = (df["tipo_diagnostico"] == t).sum()
        print(f"  Tipo {t}: {n} pacientes ({n/len(df)*100:.1f}%)")

    print(f"\nTop 5 pacientes más urgentes (score_dinamico):")
    cols = ["id_paciente", "Diag", "Urg", "Sever", "dias_en_lista",
            "score_dinamico", "vulnerabilidad", "grupo_prioridad"]
    print(df.nlargest(5, "score_dinamico")[cols].to_string(index=False))
    print()


# ─────────────────────────────────────────────────────────────────────────────
# 10. PUNTO DE ENTRADA
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)

    print("Generando dataset de pacientes (fiel al paper)...\n")
    df = generar_pacientes(n=200, semilla=42)

    df.to_csv("data/pacientes.csv", index=False, encoding="utf-8-sig")
    df.to_json("data/pacientes.json", orient="records", indent=2, force_ascii=False)

    print("Guardado en: data/pacientes.csv")
    print("Guardado en: data/pacientes.json")

    imprimir_resumen(df)
    validar_contra_ejemplo_paper()
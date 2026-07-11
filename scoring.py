"""
================================================================================
 SCORING — Módulo común de funciones de riesgo del paper
================================================================================
Implementación única de:
  - alpha_dinamico(...)  -> α̃(k,h), Sección 3.4.2
  - score_estatico(...)  -> sp, Ecuación (3)
  - score_dinamico(...)  -> s'p(t), Sección 3.4.2
  - vulnerabilidad(...)  -> vp(t), Ecuación (4)

Objetivo: que TODOS los algoritmos del proyecto (Greedy y Weighted A*) calculen
el riesgo de un paciente exactamente de la misma forma. Antes de este módulo,
cada enfoque tenía su propia copia de estas fórmulas (con el riesgo de que se
fueran desincronizando, como ya pasó: el wA* tenía sus propios lambdas y su
propia tabla alpha, distintos a los de config_modelo.py). A partir de ahora,
tanto Greedy como wA* deben importar estas funciones desde aquí en vez de
reimplementarlas.

Los parámetros del modelo (pesos, alphas, lambdas, tipos de diagnóstico) viven
en config_modelo.py; este módulo solo contiene las fórmulas matemáticas.
================================================================================
"""

from config_modelo import (
    PESOS,
    ALPHA,
    VARIABLES_DEPENDIENTES_TIEMPO,
    TIPO_DIAGNOSTICO,
    LAMBDA_POR_TIPO,
)


def alpha_dinamico(alpha_0: float, lambdas_tipo: list, t_dias: float) -> float:
    """
    α̃(k,h) — Sección 3.4.2 del paper:

        α̃(k,h) = (1 + (k/d_h) * λ(h)) * α̃(d_{h-1}, h-1)

    con 4 intervalos: h1=[0,90], h2=(90,180], h3=(180,360], h4=(360,540].

    lambdas_tipo: lista [λ(1), λ(2), λ(3), λ(4)], los 4 factores de
    empeoramiento del tipo de diagnóstico correspondiente (ver
    config_modelo.LAMBDA_POR_TIPO).

    Recibe la lista de lambdas directamente (en vez de un tipo de diagnóstico)
    para que cualquier algoritmo (Greedy, wA*) pueda reutilizar esta misma
    función sin depender de cómo cada uno modela sus pacientes.
    """
    lam = lambdas_tipo
    t = min(t_dias, 540)  # el paper opera hasta 540 días como límite

    if t <= 90:
        return (1 + (t / 90) * lam[0]) * alpha_0
    a90 = (1 + lam[0]) * alpha_0
    if t <= 180:
        return (1 + ((t - 90) / 90) * lam[1]) * a90
    a180 = (1 + lam[1]) * a90
    if t <= 360:
        return (1 + ((t - 180) / 180) * lam[2]) * a180
    a360 = (1 + lam[2]) * a180
    return (1 + ((t - 360) / 180) * lam[3]) * a360


def score_estatico(paciente: dict) -> float:
    """
    sp — Ecuación (3) del paper: sp = Σ wi * αi,p   (sin componente temporal)
    """
    return sum(PESOS[v] * ALPHA[v][paciente[v]] for v in PESOS)


def score_dinamico(paciente: dict, dias_extra: float = 0) -> float:
    """
    s'p(t) — Sección 3.4.2 del paper:
        s'p(t) = Σ_{i∈I}  wi  * αi,p          (variables NO dependientes del tiempo)
               + Σ_{i*∈I*} wi* * αi*,p(j,t)    (variables dependientes del tiempo)

    dias_extra: días adicionales desde hoy (sirve para proyectar el score
                a futuro, útil para la heurística h(n) del Weighted A*).
    """
    t_total = paciente["dias_en_lista"] + dias_extra
    tipo_diag = paciente.get("tipo_diagnostico") or TIPO_DIAGNOSTICO[paciente["Diag"]]
    lambdas_tipo = LAMBDA_POR_TIPO[tipo_diag]

    s = 0.0
    for var, w in PESOS.items():
        alpha_0 = ALPHA[var][paciente[var]]
        if var in VARIABLES_DEPENDIENTES_TIEMPO:
            s += w * alpha_dinamico(alpha_0, lambdas_tipo, t_total)
        else:
            s += w * alpha_0
    return s


def vulnerabilidad(paciente: dict, dias_extra: float = 0) -> float:
    """
    vp(t) — Ecuación (4) del paper: vp(t) = (t - fp) / Jclin_p

    vp < 1 -> no vulnerable | vp = 1 -> levemente vulnerable | vp > 1 -> vulnerable
    """
    t_total = paciente["dias_en_lista"] + dias_extra
    jclin_dias = paciente["Jclin_meses"] * 30.44
    return t_total / jclin_dias
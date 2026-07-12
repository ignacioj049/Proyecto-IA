# Proyecto IA — Priorización de pacientes en lista de espera quirúrgica

Este proyecto implementa una priorización de pacientes en lista de espera quirúrgica basada en el paper *Patients’ Prioritization on Surgical Waiting Lists: A Decision Support System*.
El sistema utiliza variables clínicas y psicosociales para calcular un score dinámico de riesgo, vulnerabilidad y prioridad de los pacientes.

Además, se implementa un enfoque greedy para construir una agenda quirúrgica bajo una restricción de horas disponibles de pabellón.

---

## Estructura del proyecto

Proyecto-IA/
├── generar_pacientes.py
├── config_modelo.py
├── scoring.py
├── data/
│   ├── pacientes.csv
│   └── pacientes.json
├── Greedy/
│   ├── algoritmo.py
│   ├── main.py
│   └── seleccion_greedy.csv
├── W_A_estrella/
│   ├── modelos.py
│   ├── traductor.py
│   ├── algoritmo.py
│   ├── evaluacion.py
│   └── main.py
├── Evaluacion/
│   ├── evaluacion_comparativa.py
│   ├── tabla_comparativa.csv
│   └── tabla_comparativa.md
└── README.md

---

## Dependencias

El proyecto utiliza `numpy` y `pandas`.

Para instalar las dependencias:

```bash
pip install numpy pandas
```

---

## Cómo ejecutar

### 1. Generar el dataset de pacientes

Desde la raíz del proyecto, ejecutar:

```bash
python generar_pacientes.py
```

Este script genera pacientes sintéticos con variables clínicas y psicosociales inspiradas en el paper. Además, calcula para cada paciente:

* score estático,
* score dinámico,
* vulnerabilidad,
* grupo de prioridad,
* tipo de diagnóstico,
* duración estimada de cirugía.

La salida se guarda en:

```text
data/pacientes.csv
data/pacientes.json
```

---

### 2. Ejecutar el algoritmo greedy

Desde la raíz del proyecto, ejecutar:

```bash
python Greedy/main.py
```

El archivo `Greedy/main.py` carga los pacientes generados, aplica el algoritmo greedy y muestra por consola la selección de pacientes.

La capacidad disponible de pabellón se define en:

```python
horas_pabellon = 8.0
```

Este valor puede modificarse en `Greedy/main.py`.

---

## Salida esperada

El algoritmo imprime una tabla con los pacientes seleccionados, incluyendo:

* ID del paciente,
* diagnóstico,
* tipo de diagnóstico,
* grupo de prioridad,
* score dinámico,
* vulnerabilidad,
* duración de la cirugía,
* días equivalentes de espera al momento de agendar,
* riesgo dinámico del paciente en su posición de agenda,
* costo estimado usado por el algoritmo greedy,
* horas restantes antes y después de seleccionar al paciente.

También muestra un resumen con:

```text
Horas disponibles
Horas usadas
Horas restantes
Uso de pabellón
Pacientes seleccionados
```

La selección final se guarda en:

```text
Greedy/seleccion_greedy.csv
```

---

## Algoritmo greedy

El algoritmo greedy implementado sigue la misma idea conceptual del enfoque wA*: minimizar el deterioro acumulado de la lista de espera. En lugar de seleccionar simplemente al paciente con mayor prioridad actual, el algoritmo evalúa localmente qué paciente conviene agendar en la posición actual de la agenda.

En cada iteración, el algoritmo considera todos los pacientes cuya cirugía cabe en el tiempo restante de pabellón. Para cada paciente factible, calcula un costo estimado compuesto por:

1. El costo acumulado de los pacientes ya seleccionados.
2. El riesgo dinámico del paciente si se agenda en la posición actual.
3. El riesgo estimado de los pacientes que quedarían pendientes después de tomar esa decisión.

El costo usado por el greedy puede describirse como:

```text
costo_estimado =
    costo_acumulado
    + riesgo_del_paciente_agendado_ahora
    + riesgo_estimado_de_los_pacientes_pendientes
```

Luego, el algoritmo selecciona al paciente que produce el menor costo estimado. Este proceso se repite hasta que no queden pacientes factibles o no quede tiempo suficiente de pabellón.

En pseudocódigo:

```text
Mientras queden pacientes y tiempo disponible:
    mejor_paciente = ninguno
    mejor_costo = infinito

    Para cada paciente pendiente:
        si su cirugía cabe en el tiempo restante:
            calcular riesgo si se agenda ahora
            estimar riesgo futuro de los pacientes restantes
            calcular costo estimado total

            si costo estimado < mejor_costo:
                actualizar mejor_paciente

    si no existe mejor_paciente:
        terminar

    seleccionar mejor_paciente
    descontar su duración del tiempo disponible
    actualizar costo acumulado
```

Este enfoque sigue siendo greedy porque toma una decisión local en cada paso y no explora todas las combinaciones posibles de agenda. Sin embargo, a diferencia de un greedy basado solo en ranking, este criterio intenta aproximar la lógica de minimización del deterioro acumulado usada por wA*.

---

## Manejo de unidades temporales

El score dinámico del paper evoluciona en función de días de espera.El algoritmo evalúa el riesgo de cada paciente usando dias_extra (días adicionales de espera clínica) directamente, sin convertir minutos de pabellón a días:

* el paciente que se agenda en el paso actual se evalúa con dias_extra = 0
* los pacientes que quedan pendientes se evalúan con dias_extra = dias_postergacion (por defecto 7: "Si no se agenda ahora, esperará una semana más")


```python
dias_postergación  = 7
```

Esto reemplaza el enfoque anterior (que convertía minutos de pabellón acumulados a días de espera vía minutos_por_dia_espera) por un criterio más simple y, sobre todo, consistente entre Greedy y Weighted A*: ambos algoritmos usan ahora exactamente el mismo criterio de dias_extra para proyectar el deterioro de los pacientes.

---

## Resultado generado

Después de ejecutar el algoritmo greedy, se genera el archivo:

```text
Greedy/seleccion_greedy.csv
```

Este archivo contiene la agenda sugerida por el algoritmo greedy para la capacidad de pabellón definida.

## Módulo común de scoring
Para que Greedy y Weighted A* jerarquicen a los pacientes de forma consistente, ambos algoritmos calculan el riesgo usando exactamente las mismas fórmulas y los mismos parámetros del modelo del paper:
* config_modelo.py centraliza los pesos wi, los valores alpha por categoría, la clasificación de diagnósticos en tipos A/B/C y los factores de empeoramiento lambda.

* scoring.py implementa score_estatico, score_dinamico, vulnerabilidad y alpha_dinamico una única vez.

Ni Greedy ni Weighted A* deben reimplementar estas fórmulas ya que ambos importan desde estos dos archivos.

## Weighted A* (W_A_estrella/)

Implementa una búsqueda informada Weighted A* (f(n) = g(n) + w·h(n)) donde:


* g(n): riesgo real acumulado de los pacientes ya agendados en la agenda
parcial (evaluados con dias_extra=0).
* h(n): heurística — riesgo estimado de los pacientes pendientes si quedan
sin agendar dias_postergacion días más (por defecto 7).
* En cada nodo solo se expanden los top_k_candidatos pacientes pendientes
que caben en el tiempo restante y que tienen mayor riesgo actual (poda
de la rama de búsqueda), y se descartan estados repetidos (mismo
subconjunto de pacientes agendados) que ya fueron visitados con un g
igual o mejor.


Por defecto, W_A_estrella/main.py corre una sola pasada (n_semanas = 1,
capacidad de un bloque de pabellón de 8h). También soporta simular varias
semanas seguidas (reinyectando a los pacientes no agendados con más días de
espera), pero para comparar contra Greedy en igualdad de condiciones se usa el
modo de una sola pasada.


## Preselección común de candidatos (top_k = 40)

Tanto Greedy/main.py como W_A_estrella/main.py aplican el mismo
preprocesamiento antes de correr su algoritmo: ordenan a todos los pacientes
por grupo_prioridad (ascendente), vulnerabilidad (descendente) y
score_dinamico (descendente), y se quedan con los primeros top_k = 40.
Esto asegura que ambos algoritmos compitan por agendar exactamente el mismo
subconjunto de 40 pacientes más prioritarios, en vez de que cada uno decida
sobre los 200 pacientes completos.

## Evaluación comparativa Greedy vs Weighted A* (Evaluacion/)

Evaluacion/evaluacion_comparativa.py es el script de evaluación común del proyecto. Ejecuta ambos algoritmos bajo condiciones idénticas para que la comparación sea válida:

* mismo dataset (generar_pacientes(n = 200, semilla=42)),
* mismo top_k (aplicado una sola vez, compartido por ambos algoritmos, replicando el criterio de ordenamiento de cada main.py),
* misma capacidad de pabellón (8hrs /480min),
* mismo dias_postergacion (7)
* mismos pesos/alphas/lambdas (ambos algoritmos ya usan config_modelo.py y scoring.py),
* ambos en modo "una sola pasada" (un único bloque de pabellón)

Para ejecutarlo, desde la raíz del proyecto:

``` bash 
python Evaluacion/evaluacion_comparativa.py

```
Métricas medidas para cada algoritmo:

* tiempo de ejecución (segundos),
* pacientes seleccionados/agendados,
* horas usadas y horas restantes de pabellón,
* costo total real de la agenda (suma del riesgo dinámico de los pacientes efectivamente agendados, evaluado con dias_extra = 0)

La tabla comparativa se guarda en:

```text
Evaluación/tabla_comparativa.csv
Evaluacion/tabla_comparativa.md
```
 

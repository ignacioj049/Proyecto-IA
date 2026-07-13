# Proyecto IA — Priorización de pacientes en lista de espera quirúrgica

Este proyecto implementa una priorización de pacientes en lista de espera quirúrgica basada en el paper *Patients' Prioritization on Surgical Waiting Lists: A Decision Support System*.
El sistema utiliza variables clínicas y psicosociales para calcular un score dinámico de riesgo, vulnerabilidad y prioridad de los pacientes.

Además, se implementan y comparan tres enfoques para construir la agenda quirúrgica semanal bajo una restricción de horas disponibles de pabellón: un baseline FIFO (orden estricto de llegada), un enfoque greedy, y un enfoque Weighted A* que busca minimizar el deterioro acumulado de toda la lista de espera.

---

## Estructura del proyecto

```text
Proyecto-IA/
├── generar_pacientes.py
├── config_modelo.py
├── scoring.py
├── simulacion.py
├── data/
│   ├── pacientes.csv
│   └── pacientes.json
├── FIFO/
│   ├── algoritmo.py
│   ├── main.py
│   └── seleccion_fifo.csv
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
```

---

## Dependencias

El proyecto utiliza `numpy`, `pandas` y `tabulate` 

Para instalar las dependencias:

```bash
pip install numpy pandas tabulate
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

### 2. Ejecutar el algoritmo FIFO

Desde la raíz del proyecto, ejecutar:

```bash
python FIFO/main.py
```

El archivo `FIFO/main.py` carga los 200 pacientes generados y simula, semana a semana, la construcción de la agenda quirúrgica agendando siempre a los pacientes con mayor tiempo en lista de espera primero, sin considerar score dinámico ni vulnerabilidad. Sirve como punto de referencia mínimo frente a los otros dos enfoques.

La capacidad disponible de pabellón y los días de postergación por semana se definen en:

```python
horas_pabellon = 8.0
dias_postergacion = 7
```

La selección semanal se guarda en:

```text
FIFO/seleccion_fifo.csv
```

---

### 3. Ejecutar el algoritmo greedy

Desde la raíz del proyecto, ejecutar:

```bash
python Greedy/main.py
```

El archivo `Greedy/main.py` carga los 200 pacientes generados y simula, semana a semana, la construcción de la agenda aplicando el algoritmo greedy de minimización de costo acumulado (ver sección "Algoritmo greedy" más abajo).

La capacidad disponible de pabellón se define en:

```python
horas_pabellon = 8.0
```

Este valor puede modificarse en `Greedy/main.py`.

La selección semanal se guarda en:

```text
Greedy/seleccion_greedy.csv
```

`Greedy/algoritmo.py` incluye además una segunda función, `greedy_priorizacion_paper`, que replica el procedimiento de selección de la Sección 3.5 del paper (clasificación de pacientes en 4 grupos según su score dinámico y vulnerabilidad, cruzados con el tipo de diagnóstico A/B/C). Esta variante es la que se usa como referencia "fiel al paper" en el script de comparación.

---

### 4. Ejecutar el Weighted A*

Desde la raíz del proyecto, ejecutar:

```bash
python W_A_estrella/main.py
```

El archivo `W_A_estrella/main.py` carga los 200 pacientes generados y ejecuta, semana a semana, una búsqueda Weighted A* que arma la agenda quirúrgica minimizando el riesgo acumulado total, en vez de decidir localmente cuál paciente conviene agendar en cada momento.

Los parámetros del experimento se definen en `W_A_estrella/main.py`:

```python
horas_pabellon = 8
peso_w = 2.0
top_k_candidatos = 40
dias_postergacion = 7
```

---

### 5. Comparar los tres enfoques

Desde la raíz del proyecto, ejecutar:

```bash
python Evaluacion/evaluacion_comparativa.py
```

Este script corre FIFO, Greedy (replicación del paper) y Weighted A* bajo exactamente las mismas condiciones —mismo dataset de 200 pacientes, misma capacidad de pabellón, mismo `top_k_candidatos`— y genera una tabla comparativa con:

* promedio de días de espera de los pacientes al momento de ser agendados,
* número de pacientes vulnerables (`vp(t) >= 1`) que quedan sin operar,
* tiempo de cómputo total y promedio por semana,
* semanas simuladas y pacientes agendados/pendientes.

La tabla se guarda en:

```text
Evaluacion/tabla_comparativa.csv
Evaluacion/tabla_comparativa.md
```

---

## Salida esperada

Cada uno de los tres algoritmos (FIFO, Greedy, wA*) imprime por consola, semana a semana, la agenda propuesta, incluyendo:

* ID del paciente,
* diagnóstico / tipo de diagnóstico,
* score dinámico y vulnerabilidad,
* duración de la cirugía,
* días de espera acumulados al momento de agendar,
* horas restantes de pabellón antes y después de cada selección.

Al finalizar la simulación completa, cada script muestra un resumen con:

```text
Semanas simuladas
Pacientes agendados / pendientes al final
Pacientes vulnerables sin operar
Promedio de días de espera al agendar
Tiempo de cómputo total y por semana
```

---

## Algoritmo greedy

El algoritmo greedy implementado en `greedy_priorizacion` sigue la misma idea conceptual del enfoque wA*: minimizar el deterioro acumulado de la lista de espera. En lugar de seleccionar simplemente al paciente con mayor prioridad actual, el algoritmo evalúa localmente qué paciente conviene agendar en la posición actual de la agenda.

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

Para que el algoritmo escale sobre los 200 pacientes reales (es O(N²) por semana), `greedy_priorizacion` acepta un parámetro opcional `top_k_candidatos` que acota, antes de iterar, cuántos pacientes se consideran como candidatos esa semana — la misma idea que usa `top_k_candidatos` en el Weighted A* para acotar la rama de búsqueda por nodo.

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

La función `greedy_priorizacion_paper`, en cambio, no calcula ningún costo: reproduce directamente el procedimiento de selección de la Sección 3.5 del paper, clasificando a los pacientes en 4 grupos (score dinámico vs. promedio, cruzado con vulnerabilidad) y 3 tipos de diagnóstico (A/B/C según velocidad de deterioro), y llenando la agenda respetando ese orden de grupos.

---

## Algoritmo FIFO

El algoritmo FIFO implementado en `fifo_priorizacion` no usa ningún criterio clínico: ordena a los pacientes pendientes por `dias_en_lista` de mayor a menor, y llena la agenda en ese orden hasta agotar la capacidad de pabellón disponible. Se incluye como punto de comparación mínimo frente a Greedy y wA*.

---

## Simulación multi-semana

Los tres algoritmos comparten la misma mecánica de simulación semanal, implementada en `simulacion.py` para FIFO y Greedy, y directamente en `W_A_estrella/main.py` para wA*: en cada semana se arma una agenda con los pacientes pendientes según la capacidad de pabellón disponible, se retira de la lista a los agendados, y se avanza en `dias_postergacion` días la espera de los pacientes que quedaron pendientes, quienes vuelven a competir la semana siguiente con su score dinámico y vulnerabilidad recalculados. La simulación continúa hasta agendar a todos los pacientes o alcanzar un tope de seguridad de semanas.

Para que la búsqueda o el costeo de cada semana no crezca sin control sobre la población completa de pacientes pendientes, tanto wA* como Greedy aceptan un parámetro `top_k_candidatos`: acota cuántos pacientes se consideran como candidatos EN ESA semana puntual (la rama de decisión), pero no descarta a nadie de la lista de espera real — los pacientes que quedan fuera del top_k de una semana siguen pendientes y vuelven a competir la semana siguiente, con más días de espera acumulados.

---

## Manejo de unidades temporales

El score dinámico del paper evoluciona en función de días de espera. Por esta razón, los algoritmos convierten el tiempo quirúrgico acumulado a días equivalentes antes de proyectar el deterioro de los pacientes.

Por defecto se utiliza:

```python
minutos_por_dia_espera = 480
```

Esto interpreta una jornada quirúrgica de 8 horas como un día equivalente de espera dentro de la simulación. Esta conversión evita mezclar directamente minutos de cirugía con días de evolución clínica.

---

## Resultado generado

Después de ejecutar cada algoritmo, se generan los siguientes archivos:

```text
FIFO/seleccion_fifo.csv
Greedy/seleccion_greedy.csv
Evaluacion/tabla_comparativa.csv
Evaluacion/tabla_comparativa.md
```

El primero y el segundo contienen el historial semanal de la simulación de FIFO y Greedy respectivamente. Los dos últimos contienen la tabla comparativa entre FIFO, Greedy (replicación del paper) y Weighted A*, con las métricas descritas en la sección "Comparar los tres enfoques".
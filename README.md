# Proyecto IA — Priorización de pacientes en lista de espera quirúrgica

Este proyecto implementa una priorización de pacientes en lista de espera quirúrgica basada en el paper *Patients’ Prioritization on Surgical Waiting Lists: A Decision Support System*.
El sistema utiliza variables clínicas y psicosociales para calcular un score dinámico de riesgo, vulnerabilidad y prioridad de los pacientes.

Además, se implementa un enfoque greedy para construir una agenda quirúrgica bajo una restricción de horas disponibles de pabellón.

---

## Estructura del proyecto

```text
Proyecto-IA/
├── generar_pacientes.py
├── data/
│   ├── pacientes.csv
│   └── pacientes.json
├── Greedy/
│   ├── algoritmo.py
│   ├── main.py
│   └── seleccion_greedy.csv
└── README.md
```

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

El score dinámico del paper evoluciona en función de días de espera. Por esta razón, el algoritmo convierte el tiempo quirúrgico acumulado a días equivalentes antes de proyectar el deterioro de los pacientes.

Por defecto se utiliza:

```python
minutos_por_dia_espera = 480
```

Esto interpreta una jornada quirúrgica de 8 horas como un día equivalente de espera dentro de la simulación. Esta conversión evita mezclar directamente minutos de cirugía con días de evolución clínica.

---

## Resultado generado

Después de ejecutar el algoritmo greedy, se genera el archivo:

```text
Greedy/seleccion_greedy.csv
```

Este archivo contiene la agenda sugerida por el algoritmo greedy para la capacidad de pabellón definida.


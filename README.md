## Cómo ejecutar

El proyecto implementa una priorización de pacientes en lista de espera quirúrgica basada en el paper *Patients’ Prioritization on Surgical Waiting Lists: A Decision Support System*. Primero se genera un dataset sintético de pacientes y luego se aplica un algoritmo greedy para seleccionar pacientes según la capacidad disponible de pabellón.

### Estructura del proyecto

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

### 1. Instalar dependencias

El proyecto utiliza `numpy` y `pandas`.

```bash
pip install numpy pandas
```

### 2. Generar el dataset de pacientes

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

### 3. Ejecutar el algoritmo greedy

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

### 4. Salida esperada

El algoritmo imprime una tabla con los pacientes seleccionados, incluyendo:

* ID del paciente,
* diagnóstico,
* tipo de diagnóstico,
* grupo de prioridad,
* score dinámico,
* vulnerabilidad,
* duración de la cirugía,
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

## Algoritmo greedy

El algoritmo greedy selecciona pacientes de manera secuencial según un ranking de prioridad. Los pacientes se ordenan usando los siguientes criterios:

1. Grupo de prioridad.
2. Tipo de diagnóstico.
3. Vulnerabilidad.
4. Score dinámico.

La prioridad de diagnóstico se define como:

```text
Tipo A → mayor prioridad, diagnóstico que empeora rápido
Tipo B → prioridad intermedia
Tipo C → menor prioridad, diagnóstico que empeora lentamente
```

Luego, el algoritmo recorre la lista ordenada y selecciona a un paciente si su cirugía cabe dentro de las horas restantes de pabellón.

En pseudocódigo:

```text
Ordenar pacientes por grupo, tipo de diagnóstico, vulnerabilidad y score dinámico

Mientras queden pacientes por revisar:
    tomar el siguiente paciente más prioritario

    si la duración de su cirugía cabe en el tiempo restante:
        seleccionar paciente
        descontar duración de cirugía

    si no cabe:
        saltar al siguiente paciente

Finalizar cuando no queden pacientes factibles o no quede tiempo suficiente
```

Este enfoque no explora todas las combinaciones posibles de pacientes. En cambio, toma en cada paso la mejor decisión local según el ranking definido. Por eso corresponde a una heurística greedy.


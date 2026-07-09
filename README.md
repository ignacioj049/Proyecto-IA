# Proyecto-IA

## Cómo ejecutar

Este proyecto implementa una estrategia de priorización de pacientes en lista de espera quirúrgica usando un enfoque greedy. El flujo general es:

1. Generar un dataset sintético de pacientes.
2. Calcular el score biopsicosocial dinámico y la vulnerabilidad de cada paciente.
3. Aplicar el algoritmo greedy para seleccionar pacientes según las horas disponibles de pabellón.
4. Guardar la selección final en un archivo CSV.

### Estructura del proyecto

```text
Proyecto-IA/
├── generar_pacientes.py
├── Greedy/
│   └── greedy_priorizacion.py
└── README.md
```

### 1. Instalar dependencias

El proyecto utiliza `pandas` y `numpy`. Para instalarlas:

```bash
pip install pandas numpy
```

### 2. Generar el dataset de pacientes

Desde la raíz del proyecto, ejecutar:

```bash
python generar_pacientes.py
```

Esto genera los archivos:

```text
data/pacientes.csv
data/pacientes.json
```

Estos archivos contienen pacientes sintéticos con sus variables biopsicosociales, score estático, score dinámico, vulnerabilidad y grupo de prioridad.

### 3. Ejecutar el algoritmo greedy

Desde la raíz del proyecto, ejecutar:

```bash
python Greedy/greedy_priorizacion.py
```

El algoritmo selecciona pacientes considerando una cantidad fija de horas disponibles de pabellón. Actualmente, la capacidad usada es:

```python
horas_pabellon = 8.0
```

Esta variable puede modificarse dentro del archivo `Greedy/greedy_priorizacion.py`.

### 4. Salida esperada

Al ejecutar el algoritmo greedy, se muestra por consola la lista de pacientes seleccionados, junto con un resumen como:

```text
Horas disponibles
Horas usadas
Horas restantes
Uso de pabellón
Pacientes seleccionados
```

Además, se genera un archivo CSV con la selección final:

```text
Greedy/seleccion_greedy.csv
```

### Criterio greedy utilizado

El algoritmo ordena los pacientes según los siguientes criterios:

1. Grupo de prioridad.
2. Tipo de diagnóstico.
3. Vulnerabilidad.
4. Score dinámico.

Luego recorre la lista ordenada y selecciona a un paciente si su cirugía cabe dentro de las horas restantes de pabellón. El proceso termina cuando no quedan horas suficientes o no hay más pacientes factibles.

En términos generales, el criterio greedy puede resumirse como:

```text
Mientras queden horas disponibles:
    tomar el siguiente paciente más prioritario
    si su cirugía cabe en el tiempo restante:
        seleccionarlo
        descontar su duración
```

Este enfoque no busca evaluar todas las combinaciones posibles de pacientes, sino seleccionar localmente la mejor opción disponible en cada paso según el ranking definido.

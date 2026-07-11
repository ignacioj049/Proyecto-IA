from config_modelo import ALPHA

def traducir_valor(variable: str, valor):
    if variable in ALPHA:
        clave = valor if valor in ALPHA[variable] else str(valor)
        if clave in ALPHA[variable]:
            return ALPHA[variable][clave]
        print(f"  [!] Advertencia: '{valor}' no encontrado en '{variable}'. Asignando 0.0")
        return 0.0
    if isinstance(valor, (int, float)):
        return float(valor)
    return 0.0
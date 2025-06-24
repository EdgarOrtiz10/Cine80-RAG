
"""
Utilidades generales para validación de datos, incluyendo verificación de vectores numéricos.
"""
import math
from typing import List

def es_vector_valido(vector) -> bool:
    """
    Verifica si el vector es válido:
    - No es None
    - Es una lista o tupla
    - Tiene al menos un valor numérico
    """
    return isinstance(vector, (list, tuple)) and len(vector) > 0 and all(isinstance(v, (int, float)) for v in vector)

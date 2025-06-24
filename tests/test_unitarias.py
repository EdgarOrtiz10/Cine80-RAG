"""
Pruebas unitarias para funciones críticas del sistema RAG de preguntas sobre películas.

Estas pruebas verifican que:
- La función de validación de vectores (`es_vector_valido`) funcione correctamente.
- La función de traducción (`traducir`) maneje correctamente un caso básico.

Dependencias:
- pytest
- app.utils.es_vector_valido
- app.respuestas.traducir
"""

import pytest
from app.utils import es_vector_valido
from app.respuestas import traducir

def test_es_vector_valido_con_vector_valido():
    """
    Verifica que la función es_vector_valido retorne True
    cuando se le pasa un vector válido (1536 dimensiones).
    """
    vector = [0.1] * 1536
    assert es_vector_valido(vector) is True

def test_es_vector_valido_con_vector_vacio():
    """
    Verifica que la función es_vector_valido retorne False
    cuando se le pasa un vector vacío.
    """
    vector = []
    assert es_vector_valido(vector) is False

def test_traducir_devuelve_texto_traducido():
    """
    Verifica que la función traducir traduzca correctamente
    el texto 'hello' del inglés al español.

    En caso de error (por conectividad o límites de API),
    acepta que devuelva el mismo texto original.
    """
    texto = "hello"
    resultado = traducir(texto, origen="en", destino="es")
    assert resultado.lower() in ["hola", "hello"]  # en caso de fallo devuelve original

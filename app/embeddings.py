"""
Módulo para generar embeddings de texto utilizando la API de OpenAI,
incluyendo validación para evitar valores fuera de rango.
"""

import os
from dotenv import load_dotenv
from app.utils import es_vector_valido
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

# Crear cliente sin pasar api_key explícitamente
client = OpenAI()  # ✅ Lee la API Key desde la variable de entorno

def generar_embedding(texto: str) -> list:
    """
    Genera un vector de embedding para un texto dado usando OpenAI,
    y valida que no tenga valores fuera de rango.

    Args:
        texto (str): Texto de entrada.

    Returns:
        list: Lista de números flotantes representando el embedding.

    Raises:
        ValueError: Si el embedding generado contiene valores inválidos.
    """
    respuesta = client.embeddings.create(
        input=texto,
        model="text-embedding-ada-002"
    )

    embedding = respuesta.data[0].embedding

    if not es_vector_valido(embedding):
        raise ValueError("El embedding contiene valores no válidos (NaN o infinitos)")

    return embedding

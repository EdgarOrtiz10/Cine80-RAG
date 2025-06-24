"""
Módulo para interpretar preguntas abiertas y responder con base en el contenido
semántico de las películas almacenadas en la base de datos PostgreSQL.

Usa embeddings para encontrar las películas más relevantes y generar una
respuesta profesional y natural con su información.
"""

import os
from openai import OpenAI
from app.db import obtener_conexion
from app.embeddings import generar_embedding
from app.utils import es_vector_valido
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def traducir(texto: str, origen='auto', destino='es') -> str:
    """Traduce un texto al idioma deseado (por defecto: español)."""
    try:
        return GoogleTranslator(source=origen, target=destino).translate(texto)
    except Exception:
        return texto  # En caso de error, retorna el texto original

def generar_respuesta_con_gpt(pregunta: str, contexto: str, titulo: str, imagen: str) -> str:
    """
    Usa GPT para generar una respuesta profesional basada en una descripción de película,
    adaptándose a si el usuario pide imagen, título u otra información.
    """
    prompt = f"""
Eres un experto en cine y redactor profesional.

El usuario ha hecho la siguiente pregunta: "{pregunta}"

Datos disponibles sobre una película relacionada:
- Título: {titulo}
- Descripción: {contexto}
- Imagen (URL): {imagen}

Instrucciones:
- Tu única fuente de información es la que se te proporciona.
- No busques en fuentes externas ni utilices conocimientos previos.
- No puedes inventar detalles o mencionar películas no incluidas en los datos disponibles.
- Si la pregunta es similar a "Muestre la imagen relacionada a la película...", muéstrale solamente Imagen (URL).
- Si pide solo el título, responde solo con el título.
- Si pregunta sobre la trama, actores u otra información, responde con una redacción fluida y profesional.
- No repitas "Título:", "Descripción:", etc., a menos que el usuario lo pida explícitamente.
- Si es apropiado, puedes incluir la URL de la imagen al final entre paréntesis.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=250
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error al generar respuesta: {e}]"

def responder_pregunta(pregunta: str) -> str:
    vector = generar_embedding(pregunta)

    if not es_vector_valido(vector):
        return "Lo siento, no pude interpretar tu pregunta correctamente."

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT titulo, image, descripcion, 1 - (embedding <=> %s) AS similitud
        FROM peliculas
        ORDER BY embedding <=> %s
        LIMIT 1
    """, (vector, vector))

    resultado = cursor.fetchone()
    cursor.close()
    conexion.close()

    if not resultado:
        return "No encontré información relacionada con tu pregunta."

    titulo, imagen, descripcion, similitud = resultado

    if similitud < 0.80 or not all([titulo, imagen, descripcion]):
        return "No encontré información relacionada con tu pregunta."

    return generar_respuesta_con_gpt(pregunta, descripcion, titulo, imagen)

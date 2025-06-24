"""
Módulo para gestionar la conexión a PostgreSQL y configurar la tabla con PGVector.
"""

import psycopg2
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()
CADENA_CONEXION = os.getenv("DATABASE_URL")

def obtener_conexion():
    """
    Establece una conexión a la base de datos PostgreSQL.

    Returns:
        psycopg2.extensions.connection: Objeto de conexión activo.
    """
    return psycopg2.connect(CADENA_CONEXION)

def crear_tabla_y_extension():
    """
    Crea la extensión PGVector (si no existe) y la tabla 'peliculas'
    que contendrá título, descripción y el embedding vectorial.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    # Crear la extensión y la tabla si no existen
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS peliculas (
            id SERIAL PRIMARY KEY,
            titulo TEXT,
            image TEXT,
            descripcion TEXT,
            embedding vector(1536)
        );
    """)
    
    conexion.commit()
    cursor.close()
    conexion.close()

def guardar_embedding(texto: str, embedding: list):
    """
    Guarda el texto y su embedding en la tabla 'peliculas'.

    Args:
        texto (str): Texto de entrada o descripción.
        embedding (list): Vector de embedding generado por OpenAI.
    """
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO peliculas (descripcion, embedding)
        VALUES (%s, %s)
    """, (texto, embedding))

    conexion.commit()
    cursor.close()
    conexion.close()
    print("✅ Embedding guardado correctamente en la base de datos.")

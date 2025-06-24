"""
Repositorio concreto que implementa la interfaz PeliculaRepository 
utilizando PostgreSQL y pgvector para realizar búsquedas semánticas.
"""


from app.db import obtener_conexion
from domain.models import Pelicula
from interfaces.pelicula_repository import PeliculaRepository

class PGRepository(PeliculaRepository):
    def buscar_pelicula_mas_cercana(self, vector: list) -> Pelicula:
        conexion = obtener_conexion()
        cursor = conexion.cursor()

        cursor.execute("""
            SELECT titulo, image, descripcion, embedding <-> (%s::vector) AS distancia
            FROM peliculas
            ORDER BY distancia ASC
            LIMIT 1
        """, (vector,))

        resultado = cursor.fetchone()
        cursor.close()
        conexion.close()

        if not resultado:
            return None

        titulo, image, descripcion, distancia = resultado
        return Pelicula(titulo, descripcion, image, distancia)

    def insertar_pelicula(self, titulo, descripcion, imagen, vector):
        conexion = obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            INSERT INTO peliculas (titulo, image, descripcion, embedding)
            VALUES (%s, %s, %s, %s)
        """, (titulo, imagen, descripcion, vector))
        conexion.commit()
        cursor.close()
        conexion.close()

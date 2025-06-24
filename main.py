"""
Script principal que inicializa la base de datos y ejecuta el proceso de indexación.
"""

from app.db import crear_tabla_y_extension
from app.indexer import indexar_peliculas
from app.db import guardar_embedding
from app.embeddings import generar_embedding


def main():
    crear_tabla_y_extension()
    indexar_peliculas()

if __name__ == "__main__":
    main()

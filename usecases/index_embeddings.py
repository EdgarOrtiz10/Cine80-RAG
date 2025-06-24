"""
Script principal que inicializa la base de datos y ejecuta el proceso de indexación.
"""

import os
import sys

# Asegura que el path raíz del proyecto esté incluido
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db import crear_tabla_y_extension
from app.indexer import indexar_peliculas
from app.db import guardar_embedding
from app.embeddings import generar_embedding


def main():
    crear_tabla_y_extension()
    indexar_peliculas()

if __name__ == "__main__":
    main()

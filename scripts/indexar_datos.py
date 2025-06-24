"""
Script ejecutable para indexar películas desde un archivo CSV a la base de datos.
Este script carga los datos, genera los embeddings y los guarda en la tabla `peliculas`.

"""

import sys
import os

# Agrega la carpeta raíz al path para que se puedan importar los módulos internos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.indexer import indexar_peliculas

if __name__ == "__main__":
    ruta_csv = "data/movies-dataset.csv"
    print(f"Iniciando indexación de películas desde: {ruta_csv}")
    indexar_peliculas(ruta_csv)

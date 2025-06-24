"""
Módulo encargado de leer un archivo CSV con descripciones de películas,
generar embeddings y almacenarlos en la base de datos PostgreSQL.
"""

from data.data_request import movies_dataset
from app.db import obtener_conexion
from app.embeddings import generar_embedding
from app.utils import es_vector_valido

def indexar_peliculas():
    """
    Carga el dataset de películas desde una URL remota,
    genera embeddings y los guarda en la base de datos.
    """
    try:
        df = movies_dataset()
    except Exception as e:
        print(f"Error al leer el dataset: {e}")
        return

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    total = len(df)
    exitosos = 0

    for _, fila in df.iterrows():
        titulo = str(fila.get('title', '')).strip()
        image = str(fila.get("image", "")).strip()
        descripcion = str(fila.get('plot', '')).strip()
        
        if not titulo or not descripcion or not image:
            print("ERROR: Registro con datos incompletos. Se omite.")
            continue

        try:
            texto = f"{titulo}. {descripcion}"
            vector = generar_embedding(texto)

            if not es_vector_valido(vector):
                print(f"⚠️ Embedding inválido para '{titulo}'. Se omite.")
                continue

            cursor.execute("""
                INSERT INTO peliculas (titulo, image, descripcion, embedding)
                VALUES (%s, %s, %s, %s)
            """, (titulo, image, descripcion, vector))

            exitosos += 1
            print(f"✅ '{titulo}' indexado correctamente.")
        except Exception as e:
            print(f"ERROR procesando '{titulo}': {e}")

    conexion.commit()
    cursor.close()
    conexion.close()

    print(f"\n📊 Proceso completado: {exitosos} de {total} películas fueron indexadas correctamente.")

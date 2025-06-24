"""
Caso de uso que se encarga de indexar todas las películas en la base de datos.
"""


def indexar_peliculas(df, repo, embedder):
    total = len(df)
    exitosos = 0

    for _, fila in df.iterrows():
        titulo = str(fila.get('title', '')).strip()
        descripcion = str(fila.get('plot', '')).strip()
        imagen = str(fila.get('image', '')).strip()

        if not titulo or not descripcion or not imagen:
            continue

        texto = f"{titulo}. {descripcion}"
        vector = embedder.generar_embedding(texto)
        repo.insertar_pelicula(titulo, descripcion, imagen, vector)
        exitosos += 1

    return exitosos, total

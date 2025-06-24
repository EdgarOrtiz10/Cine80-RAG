"""
Caso de uso que orquesta la respuesta a una pregunta en lenguaje natural,
haciendo uso del embedding y consulta en la base de datos.
"""


from interfaces.embedding_provider import EmbeddingProvider
from interfaces.pelicula_repository import PeliculaRepository


def responder_pregunta(pregunta: str, repo: PeliculaRepository, embedder: EmbeddingProvider) -> str:
    vector = embedder.generar_embedding(pregunta)
    pelicula = repo.buscar_pelicula_mas_cercana(vector)

    if not pelicula:
        return "No encontré una película relacionada."

    return f"""
🔎 Resultado relacionado:

🎬 *{pelicula.titulo}*
📸 Imagen: {pelicula.imagen}
📝 {pelicula.descripcion or 'Descripción no disponible.'}
""".strip()

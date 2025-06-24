"""
Script auxiliar para probar el proceso de indexación de forma local o manual.
"""


from data.data_request import movies_dataset
from usecases.indexar_peliculas import indexar_peliculas
from infrastructure.openai_embeddings import OpenAIEmbedder
from infrastructure.pg_peliculas import PGRepository

if __name__ == "__main__":
    df = movies_dataset()
    embedder = OpenAIEmbedder()
    repo = PGRepository()

    exitosos, total = indexar_peliculas(df, repo, embedder)
    print(f"📊 Se indexaron {exitosos} de {total} películas correctamente.")

"""
Obtiene el dataset de películas desde el repositorio remoto de GitHub.
"""
import pandas as pd

def movies_dataset():
    url = "https://raw.githubusercontent.com/EdgarOrtiz10/knowledge_base_movie/refs/heads/main/movies-dataset.csv"

    df = pd.read_csv(url)
    
    return df


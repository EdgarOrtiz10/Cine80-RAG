import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()  # ✅ NO PASAMOS api_key directamente

def generar_embedding(texto: str) -> list:
    response = client.embeddings.create(
        input=texto,
        model="text-embedding-ada-002"
    )
    return response.data[0].embedding

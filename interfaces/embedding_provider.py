"""
Interfaz que define el contrato para generar embeddings a partir de texto.
"""


from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    @abstractmethod
    def generar_embedding(self, texto: str) -> list:
        pass

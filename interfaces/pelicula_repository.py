"""
Interfaz que define el contrato para buscar e insertar películas.
"""


from abc import ABC, abstractmethod
from domain.models import Pelicula

class PeliculaRepository(ABC):
    @abstractmethod
    def buscar_pelicula_mas_cercana(self, vector: list) -> Pelicula:
        pass

    @abstractmethod
    def insertar_pelicula(self, titulo: str, descripcion: str, imagen: str, vector: list) -> None:
        pass

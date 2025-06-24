"""
Modelo de dominio que representa una película y sus atributos esenciales.
"""

class Pelicula:
    def __init__(self, titulo: str, descripcion: str, imagen: str, distancia: float = None):
        self.titulo = titulo
        self.descripcion = descripcion
        self.imagen = imagen
        self.distancia = distancia

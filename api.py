"""
Punto de entrada para la API REST del sistema RAG. 
Define los endpoints disponibles y conecta con los casos de uso definidos.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Literal
from app.respuestas import responder_pregunta
from main import main as ejecutar_indexado
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Modelos para /v1/chat/completions
class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: str = "gpt-3.5-turbo"

# Modelo para /questions
class PreguntaInput(BaseModel):
    pregunta: str

@app.get("/")
def root():
    return {"mensaje": "API RAG para preguntas sobre películas de los 80s. Usa POST /questions"}

@app.post("/questions")
def preguntar(input: PreguntaInput):
    respuesta = responder_pregunta(input.pregunta)
    return {"respuesta": respuesta}

@app.post("/embeddings")
def reindexar():
    ejecutar_indexado()
    return {"mensaje": "Reindexado completado correctamente"}

@app.post("/v1/chat/completions")
def completar(request: ChatRequest):
    # Extraer solo el último mensaje del usuario (simulando la lógica)
    pregunta = ""
    for mensaje in reversed(request.messages):
        if mensaje.role == "user":
            pregunta = mensaje.content
            break

    respuesta = responder_pregunta(pregunta)

    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": respuesta
                }
            }
        ]
    }

# Sistema RAG para Preguntas sobre Películas de los Años 80

Este proyecto implementa una arquitectura **RAG (Retrieval-Augmented Generation)** diseñada para responder preguntas abiertas en lenguaje natural sobre películas clásicas de los años 80. El sistema utiliza embeddings generados por OpenAI, PostgreSQL con la extensión `pgvector`, y modelos de lenguaje para generar respuestas contextuales y precisas.

---

## Tecnologías utilizadas

- **Python 3.11+**
- **FastAPI** – para el backend
- **PostgreSQL + pgvector** – almacenamiento de vectores semánticos
- **OpenAI API** – generación de embeddings y respuestas GPT-3.5
- **Uvicorn** – servidor ASGI para desarrollo
- **Pydantic** – validación de datos
- **Docker** – despliegue en servidor
- **Deep Translator** – soporte de traducción
- **Render** – despliegue frontend
- **Postman** – pruebas manuales

---

## Repositorios

- **Frontend (ChatBot Web)**: [https://github.com/EdgarOrtiz10/front_chat_bot](https://github.com/EdgarOrtiz10/front_chat_bot)
- **Base de conocimiento**: [https://github.com/EdgarOrtiz10/knowledge_base_movie](https://github.com/EdgarOrtiz10/knowledge_base_movie)
- **Frontend en vivo**: [https://chat-bot-ggyc.onrender.com/chat](https://chat-bot-ggyc.onrender.com/chat)

---

## Estructura del Proyecto

```bash
/
├── api.py                     # Entrada principal de la API FastAPI
├── requirements.txt           # Dependencias del proyecto
├── .env                       # Variables de entorno (clave OpenAI)
├── scripts/                   # Scripts para despliegue o pruebas
├── tests/                     # Pruebas unitarias y E2E
│   ├── test_unitarias.py
│   └── test_e2e_remote.py
├── app/                       # Lógica de aplicación
│   ├── db.py                  # Conexión con PostgreSQL
│   ├── embeddings.py          # Generación de vectores con OpenAI
│   ├── indexer.py             # Indexación de películas en la BD
│   └── utils.py               # Validaciones y utilidades generales
├── domain/
│   └── models.py              # Modelo de entidad 'Pelicula'
├── infrastructure/
│   └── pg_peliculas.py        # Repositorio concreto de películas (PostgreSQL)
├── interfaces/
│   └── pelicula_repository.py # Interface abstracta para el repositorio
└── usecases/
    └── index_embeddings.py    # Script para creación de tabla e indexación inicial
```

---

## Instalación

```bash
git clone <URL_DEL_REPOSITORIO>
cd <directorio_proyecto>
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Configura tu clave de OpenAI en un archivo `.env`:

```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
```

---

## Inicializar base de datos e indexar películas

Asegúrate de tener una instancia de PostgreSQL con la extensión `pgvector` instalada.

1. Ejecuta el script para crear la tabla `peliculas` y llenar los datos con embeddings:

```bash
python usecases/index_embeddings.py
```

---

## Ejecutar la API localmente

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

La documentación Swagger estará disponible en:

- http://localhost:8000/docs

---

## Ejemplo de solicitud (Postman)

**Endpoint**

```http
POST http://18.230.58.17:8000/questions
```

**Body (raw, JSON)**

```json
{
  "pregunta": "¿Cuál es el nombre de la película, donde los humanos y las IA’s coexisten y tienen una batalla por el control de la realidad?."
}
```

**Respuesta esperada**

```json
{
  "respuesta": "La película se llama \"Digital Frontier\" y trata sobre un brillante programador de computadoras que descubre un mundo virtual oculto donde las IA y los humanos coexisten, desencadenando una batalla por el control de la realidad. Puedes encontrar más información sobre la película en la siguiente imagen: [Imagen](https://upload.wikimedia.org/wiki/File:Final_Frontier_Voyager.jpg)"
}
```

---

## Reindexación desde Postman

Para volver a generar todos los embeddings en la base de datos, puedes enviar esta solicitud:

**Endpoint**

```http
POST http://18.230.58.17:8000/embeddings
```

**Body (raw, JSON)**

```json
"True"
```

---

## Funcionalidad como orquestador

Este backend no solo responde preguntas, también orquesta el proceso de actualización de la base de conocimiento, ya que esta se encuentra alojada en GitHub como CSV. Esto permite reindexar dinámicamente sin intervención manual sobre la base de datos.

---

## Comandos útiles para EC2 (memorizados)

```bash
# Ver contenedores activos
docker ps -a

# Reiniciar contenedor
docker restart rag-backend

# Ver contenido de un archivo en el servidor
cat api.py

# Conectarse por SSH a EC2
ssh -i deploy/ec2-edgar.pem ubuntu@18.230.58.17

# Ejecutar script desde Git Bash (Windows)
bash scripts/nombre_script.sh

# Correr servidor de desarrollo manualmente
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

---

## Ver logs del contenedor desde EC2

Una vez conectado por SSH a tu EC2:

```bash
docker logs -f rag-backend
```

---

## Arquitectura del sistema (Diagrama de flujo)

El siguiente diagrama representa el flujo de interacción entre el usuario, el backend y el modelo de lenguaje:

![Diagrama de flujo](./Diagrama%20de%20flujo.png)

---

## Estado del proyecto

- Indexación de datos desde GitHub (base de conocimiento)
- Generación y almacenamiento de embeddings
- Búsqueda semántica con pgvector
- Respuestas generadas con GPT-3.5 contextualizadas
- Frontend funcional desplegado en Render
- API desplegada en EC2 (AWS)

---

## Contacto

**Edgar Ortiz Escudero**  
Desarrollador Backend | Ingeniero de Sistemas | Desarrollador ChatBot
[GitHub](https://github.com/EdgarOrtiz10)
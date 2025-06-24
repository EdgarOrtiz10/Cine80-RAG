"""
Pruebas E2E sobre la API remota desplegada en EC2.
"""

import requests

def test_remote_question():
    ip_public = "18.230.58.17"
    port = "8000"
    endpoint = "/questions"
    url = f"http://{ip_public}:{port}{endpoint}"
    payload = {
        "pregunta": "que es el platano maduro"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "respuesta" in data
        print("Prueba exitosa: \n", data["respuesta"])
    except Exception as e:
        print("ERROR:", e)

if __name__ == "__main__":
    test_remote_question()
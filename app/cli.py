import requests
import uuid

session_id = str(uuid.uuid4())

print("Mesa de Ayuda IA")
print("Escribe 'salir' para terminar.\n")

while True:
    message = input("Tú: ")

    if message.lower() == "salir":
        break

    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={
            "session_id": session_id,
            "message": message
        }
    )

    print("IA:", response.json()["response"])

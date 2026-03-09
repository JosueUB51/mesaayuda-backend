from openai import OpenAI
from app.config import OPENAI_API_KEY, MODEL

client = OpenAI(api_key=OPENAI_API_KEY)


def classify_intent(message: str):

    """
    Clasifica la intención del usuario.
    """

    try:

        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=20,
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": """
Eres un clasificador de intención para una Mesa de Ayuda.

Debes responder SOLO una palabra EXACTA de esta lista:

internet
vpn
correo
sistema
otro

Definiciones:

internet → problemas de conexión a red o wifi
vpn → problemas de acceso a VPN o solicitud de VPN
correo → problemas con correo institucional o solicitud de correo
sistema → fallas en sistemas internos
otro → cualquier otro caso

Responde SOLO la palabra.
"""
                },
                {
                    "role": "user",
                    "content": message
                }
            ]
        )

        raw_result = response.choices[0].message.content

        if not raw_result:
            return "otro"

        result = raw_result.strip().lower()

        if result not in ["internet", "vpn", "correo", "sistema"]:
            return "otro"

        return result

    except Exception as e:

        print("Error en classify_intent:", e)

        return "otro"
from openai import OpenAI
from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL

client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url=OPENROUTER_BASE_URL
)

def classify_intent(message: str):
    """
    Clasifica la intención del usuario en:
    internet, vpn, correo, sistema, otro
    """

    try:
        response = client.chat.completions.create(
            model=MODEL,
            max_tokens=50,          # 🔥 Bajo para ahorrar créditos
            temperature=0,          # 🔥 Determinista
            messages=[
                {
                    "role": "system",
                    "content": "Eres un clasificador de intención. Devuelve SOLO una palabra exacta."
                },
                {
                    "role": "user",
                    "content": f"""
Clasifica este mensaje en UNA de estas categorías EXACTAS:

internet
vpn
correo
sistema
otro

Mensaje:
{message}

Devuelve SOLO la palabra exacta.
"""
                }
            ]
        )

        raw_result = response.choices[0].message.content
        print("Clasificador raw:", raw_result)  # 🔍 Debug visible en consola

        if not raw_result:
            return "otro"

        result = raw_result.strip().lower()

        # 🔥 Normalización defensiva
        if "internet" in result:
            return "internet"
        if "vpn" in result:
            return "vpn"
        if "correo" in result:
            return "correo"
        if "sistema" in result:
            return "sistema"

        return "otro"

    except Exception as e:
        print("Error en classify_intent:", e)
        return "otro"

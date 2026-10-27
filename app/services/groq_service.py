import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Inicializar el cliente de Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def consultar_modelo_groq(pregunta: str) -> str:
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": pregunta}],
        model="qwen/qwen3.8-27b",
    )
    return chat_completion.choices[0].message.content
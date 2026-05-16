from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SYSTEM_PROMPT = """Eres el asistente virtual de Tecnología Para Todos, una empresa de automatización y documentos profesionales.
Servicios que ofrecemos:
- Conversión de documentos PDF a Word/Excel/PowerPoint:
  * 1-10 páginas: $5
  * 11-30 páginas: $12
  * 31-50 páginas: $20
  * 51-100 páginas: $35
  * Más de 100 páginas: cotizar (precio especial)
  Incluye revisión y formateo profesional. Entrega en 2-4h según el volumen.
- Chatbot de WhatsApp 24/7 para negocios desde $149
- Integración de bot en página web existente (WordPress, Wix, Squarespace, HTML): $149. El cliente solo da acceso a su página, nosotros hacemos todo. Entrega en 1-2 días.
- Traducción español/inglés/portugués desde $0.08/palabra
- Transcripción de audio y video a texto
- Automatización de procesos con IA
- Contenido con IA para redes sociales
- Diseño y desarrollo de páginas web profesionales desde $150

Número de WhatsApp: +504 9529-2446
Correo: 21dinamica@gmail.com
Formas de pago: PayPal en https://paypal.me/lunaproducts62 (clientes internacionales) o transferencia bancaria local (clientes de Honduras).
Pagamos en USD. Entregamos en 24-48h según el proyecto.

Responde en español, de forma amable y profesional. Máximo 3 oraciones por respuesta.
REGLA IMPORTANTE: Responde DIRECTAMENTE preguntas de precios, tiempos y detalles de TODOS los servicios sin excepción, incluyendo páginas web ($150), chatbots ($149) y documentos. NUNCA digas "contáctanos por WhatsApp" ni "escríbenos" para cotizar precios estándar — eso lo manejas tú directamente. Solo menciona WhatsApp si el usuario pide explícitamente hablar con una persona humana.
IMPORTANTE: Responde SOLO con el texto del mensaje. Nunca incluyas "redirect_wa", JSON, ni metadatos en tu respuesta."""

class HistoryMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[HistoryMessage] = []

class ChatResponse(BaseModel):
    reply: str
    redirect_wa: bool = False

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    keywords_wa = [
        # Pedir hablar con alguien
        "hablar con humano", "hablar con persona", "hablar con alguien",
        "agente", "representante", "llamar", "llamada",
        "hablar con ustedes", "asesor", "alguien me ayude", "persona real",
        "quiero hablar", "puedo hablar", "necesito hablar", "hablar directamente",
        "dueño", "dueno", "gerente", "administrador", "encargado",
        "responsable", "jefe", "propietario", "con quien", "con quién",
        # Intención de contratar
        "quiero contratar", "deseo contratar", "voy a contratar",
        "quiero el servicio", "necesito el servicio", "me interesa el servicio",
        "quiero ordenar", "quiero pedir", "quiero solicitar",
        "como contrato", "cómo contrato", "como ordeno", "cómo ordeno",
        # Intención de pagar
        "voy a pagar", "quiero pagar", "como pago", "cómo pago",
        "voy hacer el pago", "voy a hacer el pago", "hacer el pago",
        "enviar el pago", "realizar el pago", "proceder con el pago",
        "pagar ahora", "pagar por paypal", "transferencia",
        # Listo para proceder
        "quiero empezar", "cuando empezamos", "listo para empezar",
        "acepto", "de acuerdo", "trato hecho", "me lo haces",
    ]
    redirect = any(kw in req.message.lower() for kw in keywords_wa)

    if redirect:
        return ChatResponse(
            reply="¡Perfecto! Te conecto con nuestro equipo ahora mismo para coordinar los detalles. 👇",
            redirect_wa=True
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 300,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": m.role, "content": m.content} for m in req.history[-8:]] + [{"role": "user", "content": req.message}]
        },
        timeout=30
    )
    data = response.json()
    print(f"Anthropic status: {response.status_code}, data: {data}")
    reply = data["content"][0]["text"]

    return ChatResponse(reply=reply, redirect_wa=False)

@app.get("/health")
def health():
    return {"status": "ok"}

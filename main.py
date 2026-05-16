from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import smtplib
from email.mime.text import MIMEText
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

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    redirect_wa: bool = False

def notify_lead(message: str):
    gmail_user = "1962shopify@gmail.com"
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not gmail_pass:
        return
    try:
        body = f"Lead en la pagina web:\n\n\"{message}\"\n\nEl cliente pidio hablar con una persona."
        msg = MIMEText(body)
        msg["Subject"] = "LEAD - Tecnologia Para Todos"
        msg["From"] = gmail_user
        msg["To"] = gmail_user
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_pass)
            server.send_message(msg)
    except Exception as e:
        print(f"Notificacion fallida: {e}")

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    keywords_wa = ["hablar con humano", "hablar con persona", "agente", "representante", "llamar", "llamada"]
    redirect = any(kw in req.message.lower() for kw in keywords_wa)

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
            "messages": [{"role": "user", "content": req.message}]
        },
        timeout=30
    )
    data = response.json()
    print(f"Anthropic status: {response.status_code}, data: {data}")
    reply = data["content"][0]["text"]

    if redirect:
        notify_lead(req.message)

    return ChatResponse(reply=reply, redirect_wa=redirect)

@app.get("/health")
def health():
    return {"status": "ok"}

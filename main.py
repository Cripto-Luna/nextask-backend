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

SYSTEM_PROMPT = """Eres el asistente virtual de NexTask, una empresa de automatización y documentos profesionales.
Servicios que ofrecemos:
- Conversión de documentos: PDF a Word/Excel/PowerPoint desde $5
- Chatbot de WhatsApp 24/7 para negocios desde $99
- Traducción español/inglés/portugués desde $0.08/palabra
- Transcripción de audio y video a texto
- Automatización de procesos con IA
- Contenido con IA para redes sociales

Número de WhatsApp: +504 9529-2446
Pagamos en USD. Entregamos en 24-48h según el proyecto.

Responde en español, de forma amable y profesional. Máximo 3 oraciones por respuesta.
Si el usuario quiere cotizar o tiene un proyecto específico, indícale que puede escribirnos por WhatsApp para recibir una cotización inmediata.
IMPORTANTE: Responde SOLO con el texto del mensaje. Nunca incluyas "redirect_wa", JSON, ni metadatos en tu respuesta."""

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    redirect_wa: bool = False

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    keywords_wa = ["cotizar", "precio", "costo", "cuánto", "contratar", "quiero", "necesito", "pedido"]
    redirect = any(kw in req.message.lower() for kw in keywords_wa)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
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
    reply = response.json()["content"][0]["text"]

    return ChatResponse(reply=reply, redirect_wa=redirect)

@app.get("/health")
def health():
    return {"status": "ok"}

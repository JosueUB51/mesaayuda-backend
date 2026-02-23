from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import shutil

from app.agent.router import classify_intent
from app.agent.playbook_engine import run_intelligent_agent
from app.agent.memory import get_session, get_all_tickets

app = FastAPI()

# ==================================================
# 🔥 CORS CONFIGURACIÓN PRODUCCIÓN
# ==================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://o88cgw8c8o4kk8okcs088og.172.17.90.182.sslip.io"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# 📂 CONFIGURACIÓN DE CARPETAS
# ==================================================
STATIC_FOLDER = "app/static"
UPLOAD_FOLDER = "app/uploads"

os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================================================
# 📥 MODELO DE REQUEST
# ==================================================
class ChatRequest(BaseModel):
    session_id: str
    message: str

# ==================================================
# 💬 CHAT PRINCIPAL
# ==================================================
@app.post("/chat")
def chat(request: ChatRequest):
    response = run_intelligent_agent(
        request.session_id,
        request.message
    )

    if isinstance(response, dict):
        return response

    return {"response": response}

# ==================================================
# 📋 LISTAR TICKETS
# ==================================================
@app.get("/tickets")
def list_tickets():
    return get_all_tickets()

# ==================================================
# 🧪 ROOT TEST
# ==================================================
@app.get("/")
def root():
    return {"status": "Mesa de Ayuda IA funcionando correctamente"}
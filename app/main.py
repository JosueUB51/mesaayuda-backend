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
# 🔥 CORS CONFIGURACIÓN (DEV + DOCKER + FUTURO PROD)
# ==================================================
origins = [
    "http://localhost:5173",   # Vite dev
    "http://localhost:3000",   # Docker frontend
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# 📦 CONFIGURACIÓN ARCHIVOS
# ==================================================
STATIC_FOLDER = "app/static"
UPLOAD_FOLDER = "app/uploads"

os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==================================================
# 📥 MODELO REQUEST CHAT
# ==================================================
class ChatRequest(BaseModel):
    session_id: str
    message: str

# ==================================================
# 💬 CHAT PRINCIPAL
# ==================================================
@app.post("/chat")
def chat(request: ChatRequest):

    session = get_session(request.session_id)

    response = run_intelligent_agent(
        request.session_id,
        request.message
    )

    if isinstance(response, dict):
        return response

    return {"response": response}

# ==================================================
# 📄 DESCARGAR FORMATO VPN
# ==================================================
@app.get("/vpn/formato")
def descargar_formato_vpn():
    file_path = os.path.join(STATIC_FOLDER, "vpn_formato.pdf")

    if not os.path.exists(file_path):
        return {"error": "Formato no encontrado."}

    return FileResponse(
        path=file_path,
        filename="Formato_Solicitud_VPN.pdf",
        media_type="application/pdf"
    )

# ==================================================
# 📤 SUBIR FORMATO VPN
# ==================================================
@app.post("/vpn/upload")
async def upload_vpn(session_id: str = Form(...), file: UploadFile = File(...)):

    session = get_session(session_id)

    upload_dir = os.path.join(UPLOAD_FOLDER, "vpn")
    os.makedirs(upload_dir, exist_ok=True)

    file_location = os.path.join(upload_dir, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    session["vpn_form_uploaded"] = True

    return {
        "message": "Formato recibido correctamente. Su solicitud ha sido procesada y recibirá sus credenciales en su correo institucional."
    }

# ==================================================
# 📄 DESCARGAR FORMATO CORREO
# ==================================================
@app.get("/correo/formato")
def descargar_formato_correo():
    file_path = os.path.join(STATIC_FOLDER, "correo_formato.pdf")

    if not os.path.exists(file_path):
        return {"error": "Formato no encontrado."}

    return FileResponse(
        path=file_path,
        filename="Formato_Solicitud_Correo.pdf",
        media_type="application/pdf"
    )

# ==================================================
# 📤 SUBIR FORMATO CORREO
# ==================================================
@app.post("/correo/upload")
async def upload_correo(session_id: str = Form(...), file: UploadFile = File(...)):

    session = get_session(session_id)

    upload_dir = os.path.join(UPLOAD_FOLDER, "correo")
    os.makedirs(upload_dir, exist_ok=True)

    file_location = os.path.join(upload_dir, file.filename)

    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    session["correo_form_uploaded"] = True

    return {"message": "Archivo recibido correctamente"}

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
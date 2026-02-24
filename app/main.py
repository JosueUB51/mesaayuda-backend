import os
import shutil
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.agent.playbook_engine import run_intelligent_agent
from app.agent.memory import get_session  # 👈 para marcar flags

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*oaxaca\.gob\.mx"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_FOLDER = "app/static"
UPLOAD_FOLDER = "app/uploads"

os.makedirs(STATIC_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class ChatRequest(BaseModel):
    session_id: str
    message: str

# ---------------------------
# DESCARGA PDFs
# ---------------------------
@app.get("/vpn/formato")
def descargar_formato_vpn():
    path = os.path.join(STATIC_FOLDER, "vpn_formato.pdf")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "vpn_formato.pdf no encontrado en app/static"})
    return FileResponse(path, media_type="application/pdf", filename="Formato_Solicitud_VPN.pdf")


@app.get("/correo/formato")
def descargar_formato_correo():
    path = os.path.join(STATIC_FOLDER, "correo_formato.pdf")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "correo_formato.pdf no encontrado en app/static"})
    return FileResponse(path, media_type="application/pdf", filename="Formato_Solicitud_Correo.pdf")


# ---------------------------
# UPLOAD VPN
# ---------------------------
@app.post("/vpn/upload")
async def upload_vpn_form(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    # guarda archivo
    safe_name = f"{session_id}_vpn_{file.filename}"
    save_path = os.path.join(UPLOAD_FOLDER, safe_name)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # marca en sesión que ya lo subió
    session = get_session(session_id)
    session["vpn_form_uploaded"] = True

    return {"ok": True, "message": "Formato VPN subido correctamente", "file": safe_name}


# ---------------------------
# UPLOAD CORREO
# ---------------------------
@app.post("/correo/upload")
async def upload_correo_form(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    safe_name = f"{session_id}_correo_{file.filename}"
    save_path = os.path.join(UPLOAD_FOLDER, safe_name)

    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    session = get_session(session_id)
    session["correo_form_uploaded"] = True

    return {"ok": True, "message": "Formato Correo subido correctamente", "file": safe_name}


# ---------------------------
# CHAT
# ---------------------------
@app.post("/chat/")
async def chat(request: ChatRequest):
    response = run_intelligent_agent(request.session_id, request.message)
    if isinstance(response, dict):
        return response
    return {"response": response}


@app.get("/tickets/")
async def list_tickets():
    from app.agent.memory import get_all_tickets
    return get_all_tickets()


@app.get("/")
async def root():
    return {"status": "Mesa de Ayuda IA funcionando correctamente"}
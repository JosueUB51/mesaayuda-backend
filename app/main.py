import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.agent.playbook_engine import run_intelligent_agent

app = FastAPI()

# ==================================================
# 🔥 CORS CONFIGURACIÓN PRODUCCIÓN
# ==================================================
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*sslip\.io",
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
# 📄 DESCARGA DE FORMATOS (PDFs)
# ==================================================
@app.get("/vpn/formato")
def descargar_formato_vpn():
    path = os.path.join(STATIC_FOLDER, "vpn_formato.pdf")
    if not os.path.exists(path):
        return JSONResponse(
            status_code=404,
            content={"error": "Archivo vpn_formato.pdf no encontrado en app/static"}
        )
    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="Formato_Solicitud_VPN.pdf"
    )

@app.get("/correo/formato")
def descargar_formato_correo():
    path = os.path.join(STATIC_FOLDER, "correo_formato.pdf")
    if not os.path.exists(path):
        return JSONResponse(
            status_code=404,
            content={"error": "Archivo correo_formato.pdf no encontrado en app/static"}
        )
    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="Formato_Solicitud_Correo.pdf"
    )

# ==================================================
# 💬 CHAT PRINCIPAL
# ==================================================
@app.post("/chat/")
async def chat(request: ChatRequest):
    response = run_intelligent_agent(request.session_id, request.message)

    if isinstance(response, dict):
        return response

    return {"response": response}

# ==================================================
# 📋 LISTAR TICKETS
# ==================================================
@app.get("/tickets/")
async def list_tickets():
    # si esto te fallara porque no está importado, me avisas y lo ajusto
    from app.agent.memory import get_all_tickets
    return get_all_tickets()

# ==================================================
# 🧪 ROOT TEST
# ==================================================
@app.get("/")
async def root():
    return {"status": "Mesa de Ayuda IA funcionando correctamente"}
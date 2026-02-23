def generate_ticket(session):
    
    return {
        "categoria": session["intent"],
        "descripcion": "Incidente no resuelto automáticamente",
        "datos_recolectados": session["data"],
        "estado": "pendiente"
    }

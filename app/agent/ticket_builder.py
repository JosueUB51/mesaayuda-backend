def generate_ticket(session):
    
    return {
        "categoria": session["intent"],
        "descripcion": session.get("problem_description"),
        "datos_recolectados": session["user_data"],
        "estado": "pendiente"
    }
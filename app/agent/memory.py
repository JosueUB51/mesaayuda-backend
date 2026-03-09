sessions = {}
tickets = []

def get_session(session_id):
    if session_id not in sessions:
        sessions[session_id] = {
            "intent": None,
            "step": 0,
            "status": "welcome",   # CAMBIO PDF
            "ticket_id": None,
            "vpn_form_uploaded": False,
            "correo_form_uploaded": False,
            "user_data": {
                "nombre": None,
                "area": None,
                "edificio": None,
                "piso": None
            },
            "history": []
        }
    return sessions[session_id]

def save_ticket(ticket):
    tickets.append(ticket)

def get_all_tickets():
    return tickets
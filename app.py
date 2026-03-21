from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
REFRESH_TOKEN = "YOUR_REFRESH_TOKEN"
ORG_ID = "YOUR_ORG_ID"
DEPARTMENT_ID = "YOUR_DEPARTMENT_ID"

access_token = None
token_expiry = 0

def get_access_token():
    global access_token, token_expiry

    if access_token and time.time() < token_expiry:
        return access_token

    url = "https://accounts.zoho.in/oauth/v2/token"
    data = {
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    response = requests.post(url, data=data)
    res = response.json()

    access_token = res.get("access_token")
    expires_in = res.get("expires_in", 3600)

    token_expiry = time.time() + expires_in - 60

    return access_token

def get_headers():
    return {
        "Authorization": f"Zoho-oauthtoken {get_access_token()}",
        "orgId": ORG_ID,
        "Content-Type": "application/json"
    }

@app.route("/")
def home():
    return "Zoho Middleware Running"

@app.route("/create-ticket", methods=["POST"])
def create_ticket():
    body = request.json

    payload = {
        "subject": body.get("subject"),
        "description": body.get("description"),
        "departmentId": DEPARTMENT_ID,
        "status": body.get("status", "Open"),
        "priority": body.get("priority", "High"),
        "email": body.get("email"),
        "phone": body.get("phone"),
        "contact": {
            "lastName": body.get("contact_name"),
            "phone": body.get("contact_phone"),
            "email": body.get("contact_email")
        }
    }

    url = "https://desk.zoho.com/api/v1/tickets"
    res = requests.post(url, json=payload, headers=get_headers())

    return jsonify(res.json())

@app.route("/get-ticket-by-number", methods=["GET"])
def get_ticket_by_number():
    ticket_number = request.args.get("ticketNumber")

    url = f"https://desk.zoho.com/api/v1/tickets/search?ticketNumber={ticket_number}"
    res = requests.get(url, headers=get_headers())

    return jsonify(res.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

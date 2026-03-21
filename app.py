from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# 🔹 CONFIG
ORG_ID = "47865550"
DEPARTMENT_ID = 78127000000006907

# 🔹 GET TOKEN FROM YOUR WEBHOOK
def get_access_token():
    url = "https://financewebhook.myclassboard.com/GetZohoToken"
    res = requests.get(url).json()

    # ⚠️ adjust key if needed
    token = res.get("access_token") or res.get("token")

    if not token:
        print("Token response error:", res)
        raise Exception("Failed to get access token")

    return token

# 🔹 HEADERS
def get_headers():
    return {
        "Authorization": f"Zoho-oauthtoken {get_access_token()}",
        "orgId": ORG_ID,
        "Content-Type": "application/json"
    }

# ✅ CREATE TICKET
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

# ✅ GET TICKET BY NUMBER
@app.route("/get-ticket-by-number", methods=["GET"])
def get_ticket_by_number():
    ticket_number = request.args.get("ticketNumber")

    url = f"https://desk.zoho.com/api/v1/tickets/search?ticketNumber={ticket_number}"
    res = requests.get(url, headers=get_headers())

    return jsonify(res.json())

# ✅ HEALTH CHECK
@app.route("/")
def home():
    return "Zoho Middleware Running"

# 🚀 RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

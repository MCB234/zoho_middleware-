from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# 🔹 CONFIG
ORG_ID = "47865550"
DEPARTMENT_ID = 78127000000006907

# 🔹 GET TOKEN FROM YOUR WEBHOOK
def get_access_token():
    url = "https://financewebhook.myclassboard.com/GetZohoToken"
    
    try:
        res = requests.get(url).json()
        token = res.get("access_token") or res.get("token")

        if not token:
            print("Token error:", res)
            return None

        return token

    except Exception as e:
        print("Webhook error:", str(e))
        return None

# 🔹 HEADERS
def get_headers():
    token = get_access_token()

    if not token:
        raise Exception("No access token received")

    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "orgId": ORG_ID,
        "Content-Type": "application/json"
    }

# ✅ HEALTH CHECK
@app.route("/")
def home():
    return "Zoho Middleware Running"

# ✅ CREATE TICKET
@app.route("/create-ticket", methods=["POST"])
def create_ticket():
    try:
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

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ GET TICKET BY NUMBER
@app.route("/get-ticket-by-number", methods=["GET"])
def get_ticket_by_number():
    try:
        ticket_number = request.args.get("ticketNumber")

        url = f"https://desk.zoho.com/api/v1/tickets/search?ticketNumber={ticket_number}"
        res = requests.get(url, headers=get_headers())

        return jsonify(res.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🚀 IMPORTANT FOR RENDER (PORT FIX)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# 🔹 CONFIG
ORG_ID = "47865550"
DEPARTMENT_ID = 78127000000006907

# 🔹 GET TOKEN FROM WEBHOOK (PLAIN TEXT + TIMEOUT)
def get_access_token():
    url = "https://financewebhook.myclassboard.com/GetZohoToken"

    try:
        res = requests.get(url, timeout=5)
        token = res.text.strip()

        # remove quotes if present
        if token.startswith('"') and token.endswith('"'):
            token = token[1:-1]

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
        body = request.json or {}

        print("Incoming body:", body)

        payload = {
            "subject": body.get("subject") or "User Issue",
            "description": body.get("description") or "No description provided",
            "departmentId": DEPARTMENT_ID,
            "status": body.get("status", "Open"),
            "priority": body.get("priority", "High"),
            "email": body.get("email"),
            "phone": body.get("phone"),
            "contact": {
                "lastName": body.get("contact_name") or "Customer",
                "phone": body.get("contact_phone"),
                "email": body.get("contact_email")
            }
        }

        url = "https://desk.zoho.com/api/v1/tickets"
        res = requests.post(url, json=payload, headers=get_headers(), timeout=10)

        return jsonify(res.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ GET TICKET BY NUMBER (FIXED PARAM ISSUE)
@app.route("/get-ticket-by-number", methods=["GET"])
def get_ticket_by_number():
    try:
        # 🔥 handles both cases
        ticket_number = request.args.get("ticketNumber") or request.args.get("Ticketnumber")

        if not ticket_number:
            return jsonify({"error": "ticketNumber is required"}), 400

        url = f"https://desk.zoho.com/api/v1/tickets/search?ticketNumber={ticket_number}"
        res = requests.get(url, headers=get_headers(), timeout=10)

        return jsonify(res.json())

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🚀 RENDER PORT FIX
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

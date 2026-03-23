from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# 🔹 CONFIG
ORG_ID = "47865550"
DEPARTMENT_ID = 78127000000006907

# 🔹 TOKEN CACHE
cached_token = None
token_time = 0

def get_access_token():
    global cached_token, token_time

    try:
        if cached_token and (time.time() - token_time < 3500):
            return cached_token

        res = requests.get(
            "https://financewebhook.myclassboard.com/GetZohoToken",
            timeout=3
        )

        token = res.text.strip()

        if token.startswith('"') and token.endswith('"'):
            token = token[1:-1]

        cached_token = token
        token_time = time.time()

        print("Token refreshed")

        return token

    except Exception as e:
        print("Token error:", str(e))

        if cached_token:
            return cached_token

        return None


# 🔹 HEADERS
def get_headers():
    token = get_access_token()

    if not token:
        raise Exception("No access token available")

    return {
        "Authorization": f"Zoho-oauthtoken {token}",
        "orgId": ORG_ID,
        "Content-Type": "application/json"
    }


# ✅ HEALTH
@app.route("/")
def home():
    return "Zoho Middleware Running"


# ✅ CREATE TICKET
@app.route("/create-ticket", methods=["POST"])
def create_ticket():
    try:
        body = request.json or {}
        print("Incoming body:", body)

        headers = get_headers()

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

        print("Payload:", payload)

        url = "https://desk.zoho.com/api/v1/tickets"

        res = requests.post(url, json=payload, headers=headers, timeout=8)

        print("Zoho response:", res.text)

        return jsonify(res.json()), res.status_code

    except requests.exceptions.Timeout:
        return jsonify({"error": "Zoho API timeout"}), 504

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# ✅ GET TICKET (QUERY PARAM)
@app.route("/get-ticket-by-number", methods=["GET"])
def get_ticket_by_number():
    try:
        ticket_number = (
            request.args.get("ticketNumber")
            or request.args.get("Ticketnumber")
            or ""
        ).strip()

        if not ticket_number:
            return jsonify({"error": "Valid ticketNumber is required"}), 400

        print("Requested Ticket:", ticket_number)

        headers = get_headers()

        url = f"https://desk.zoho.com/api/v1/tickets/search?ticketNumber={ticket_number}"

        res = requests.get(url, headers=headers, timeout=6)

        if res.status_code == 204:
            return jsonify({"error": "No ticket found"}), 404

        data = res.json()

        for ticket in data.get("data", []):
            if str(ticket.get("ticketNumber")) == ticket_number:
                return jsonify(ticket)

        return jsonify({"error": "Ticket not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ 🔥 NEW: GET TICKET (PATH PARAM - FOR ELEVENLABS)
@app.route("/get-ticket/<ticket_number>", methods=["GET"])
def get_ticket_path(ticket_number):
    try:
        ticket_number = str(ticket_number).strip().replace("'", "").replace('"', "")

        if not ticket_number:
            return jsonify({"error": "Valid ticketNumber is required"}), 400

        print("Requested Ticket (PATH):", ticket_number)

        headers = get_headers()

        url = f"https://desk.zoho.com/api/v1/tickets/search?ticketNumber={ticket_number}"

        res = requests.get(url, headers=headers, timeout=6)

        if res.status_code == 204:
            return jsonify({"error": "No ticket found"}), 404

        if not res.text:
            return jsonify({"error": "Empty response"}), 500

        data = res.json()

        for ticket in data.get("data", []):
            if str(ticket.get("ticketNumber")) == ticket_number:
                return jsonify(ticket)

        return jsonify({"error": "Ticket not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🚀 RUN
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

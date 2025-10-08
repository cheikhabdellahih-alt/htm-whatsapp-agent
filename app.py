import os
import json
from flask import Flask, request, jsonify
import requests

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "REPLACE_WITH_TOKEN")
VERIFY_TOKEN   = os.environ.get("VERIFY_TOKEN", "REPLACE_WITH_VERIFY_TOKEN")
PHONE_NUMBER_ID= os.environ.get("PHONE_NUMBER_ID", "REPLACE_WITH_PHONE_NUMBER_ID")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def health():
    return {"ok": True, "service": "HTM WhatsApp-only Agent"}, 200

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def incoming():
    data = request.get_json(force=True, silent=True) or {}
    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages", [])
        if not messages:
            return jsonify(status="ignored"), 200
        msg = messages[0]
        from_wa = msg["from"]
        text = ""
        if msg.get("type") == "text":
            text = msg["text"]["body"].strip()
        reply = route_message(text)
        send_text_message(from_wa, reply)
    except Exception as e:
        print("ERROR:", e)
    return jsonify(status="ok"), 200

def route_message(text: str) -> str:
    if not text:
        return "Bonjour 👋! Comment pouvons-nous vous aider aujourd’hui chez HTM Voyages ?"
    t = text.lower()
    if "omra" in t and ("prix" in t or "tarif" in t):
        return "Nos tarifs Omra varient selon les dates et l’hébergement. Dites-nous votre période, nombre de personnes et budget."
    if "visa" in t:
        return "Pour la Omra, le visa est inclus dans nos forfaits (sous conditions). Envoyez le nombre de voyageurs et les dates prévues."
    if "contact" in t or "téléphone" in t:
        return "📞 Vous pouvez nous joindre au +22230335137. Sinon, répondez ici et nous vous assistons directement."
    return "Merci pour votre message. Pour vous proposer une option, précisez SVP: ville de départ, destination, dates, nombre de voyageurs, budget estimé."

def send_text_message(to_number: str, body: str):
    url = f"https://graph.facebook.com/v20.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"preview_url": False, "body": body}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        print("Send status:", r.status_code, r.text[:200])
    except Exception as e:
        print("Send error:", e)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))

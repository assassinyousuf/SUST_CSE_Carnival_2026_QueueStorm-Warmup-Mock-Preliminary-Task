"""
QueueStorm — CRM ticket triage web service.

Endpoints:
    GET  /health        -> simple health response
    POST /sort-ticket   -> classify one CRM ticket

Built with Flask. Stateless, no GPU, no external API calls. Safe to run on
Render / Railway / Fly / Vercel / EC2 / Poridhi Lab behind HTTPS.
"""

import os

from flask import Flask, jsonify, request

from app.classifier import classify

app = Flask(__name__)

VALID_CHANNELS = {"app", "sms", "call_center", "merchant_portal"}
VALID_LOCALES = {"bn", "en", "mixed"}


@app.get("/health")
def health():
    """Liveness probe. Must respond well within 10 seconds."""
    return jsonify({"status": "ok", "service": "queuestorm", "version": "1.0.0"}), 200


@app.post("/sort-ticket")
def sort_ticket():
    """Accept one CRM ticket and return a structured classification."""
    # Parse JSON defensively — never 500 on bad input.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    ticket_id = data.get("ticket_id")
    message = data.get("message")

    # Required fields.
    if not isinstance(ticket_id, str) or not ticket_id.strip():
        return jsonify({"error": "Field 'ticket_id' is required and must be a non-empty string."}), 400
    if not isinstance(message, str) or not message.strip():
        return jsonify({"error": "Field 'message' is required and must be a non-empty string."}), 400

    # Optional fields — validated leniently; unknown values are tolerated,
    # not rejected, so a real ticket is never dropped over an enum mismatch.
    channel = data.get("channel")
    locale = data.get("locale")
    if channel is not None and channel not in VALID_CHANNELS:
        channel = None
    if locale is not None and locale not in VALID_LOCALES:
        locale = None

    result = classify(message)
    response = {"ticket_id": ticket_id, **result}
    return jsonify(response), 200


@app.errorhandler(404)
def not_found(_):
    return jsonify({"error": "Not found. Use GET /health or POST /sort-ticket."}), 404


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "Method not allowed for this path."}), 405


if __name__ == "__main__":
    # Local dev entry point. In production, gunicorn serves app:app.
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)

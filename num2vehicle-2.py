#!/usr/bin/env python3
"""
num2vehicle.py

Render-ready HTTP API skeleton for an authorized vehicle-data service.

The original script performs a mobile-number -> vehicle lookup through a
third-party gateway. This deployment version intentionally does not expose
that sensitive lookup as a public endpoint.

Run locally:
    python num2vehicle.py

Render start command:
    gunicorn num2vehicle:app
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from flask import Flask, jsonify, request

APP_NAME = "num2vehicle"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "10000"))
API_KEY = os.getenv("API_KEY", "").strip()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(APP_NAME)

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False


def valid_mobile(value: Any) -> bool:
    """Validate an Indian-style 10-digit mobile input."""
    return isinstance(value, str) and re.fullmatch(r"[0-9]{10}", value) is not None


def authorized(req) -> bool:
    """
    Require an API key when API_KEY is configured.

    The key is read from the environment, never hard-coded into source.
    """
    if not API_KEY:
        return False

    supplied = req.headers.get("X-API-Key", "").strip()
    return supplied == API_KEY


@app.get("/")
def index():
    return jsonify(
        {
            "name": APP_NAME,
            "status": "online",
            "message": "Service is running.",
            "endpoints": ["/health", "/lookup"],
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": APP_NAME})


@app.post("/lookup")
def lookup():
    """
    Safe deployment endpoint.

    A public mobile-number -> vehicle lookup is intentionally not exposed.
    Integrate an authorized/private backend here only after establishing that
    the queried data belongs to the requesting user and that the upstream
    provider permits this use.
    """
    if not authorized(request):
        return jsonify({"status": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"status": False, "error": "JSON body required"}), 400

    mobile = str(body.get("mobile", "")).strip()
    if not valid_mobile(mobile):
        return jsonify(
            {
                "status": False,
                "error": "mobile must contain exactly 10 digits",
            }
        ), 400

    logger.info("Authorized lookup request received; identifier not logged.")

    return jsonify(
        {
            "status": False,
            "error": "Vehicle lookup is disabled in the public deployment.",
            "message": (
                "Connect an authorized/private vehicle-data backend here. "
                "Do not expose third-party personal vehicle records publicly."
            ),
        }
    ), 403


@app.errorhandler(404)
def not_found(_error):
    return jsonify({"status": False, "error": "Not found"}), 404


@app.errorhandler(405)
def method_not_allowed(_error):
    return jsonify({"status": False, "error": "Method not allowed"}), 405


@app.errorhandler(500)
def internal_error(_error):
    logger.exception("Unhandled application error")
    return jsonify({"status": False, "error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)

from flask import Flask, request, jsonify, send_from_directory
from collections import defaultdict, deque
from flask import Flask
from typing import Optional
from datetime import datetime, timedelta
import http.client
import json
import os
import random
import requests
import re

app = Flask(__name__, static_folder="static")
app = Flask(__name__, static_folder="console", static_url_path="/console")

INFOBIP_HOST = os.getenv("INFOBIP_HOST", "555q4d.api.infobip.com")
INFOBIP_API_KEY = os.getenv("INFOBIP_API_KEY", "d4c20a9f9d5b52f13f3fb36c9e91fb29-5bba29a1-f6dc-4f9b-90c8-a04c447ec20a")
INFOBIP_SENDER = os.getenv("INFOBIP_SENDER", "YourOneTimeCode@api.organizationpremises.org")

TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "0x4AAAAAAC_sC9yNMmPw6HZLXX8cS15W_CY")

OTP_EXPIRY_SECONDS = 120

RATE_LIMIT_MAX_REQUESTS = 3
RATE_LIMIT_WINDOW_SECONDS = 60

email_rate_limits = defaultdict(deque)
ip_rate_limits = defaultdict(deque)

BLOCKED_DOMAINS = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "aol.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "protonmail.com",
    "proton.me",
    "pm.me",
}

EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# very simple in-memory store for now
# move this to Redis or DB later
otp_store = {}


def get_client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "").strip()
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or "unknown"


def verify_turnstile_token(token: str, remote_ip: Optional[str] = None):
    if not TURNSTILE_SECRET_KEY:
        return False, "Turnstile secret key is missing."

    if not token:
        return False, "Security check is required."

    response = requests.post(
        "https://challenges.cloudflare.com/turnstile/v0/siteverify",
        data={
            "secret": TURNSTILE_SECRET_KEY,
            "response": token,
            "remoteip": remote_ip or ""
        },
        timeout=15
    )

    result = response.json()
    if not result.get("success"):
        error_codes = result.get("error-codes", [])
        return False, ", ".join(error_codes) or "Security check failed."

    return True, ""


def is_rate_limited(bucket, key, max_requests=RATE_LIMIT_MAX_REQUESTS, window_seconds=RATE_LIMIT_WINDOW_SECONDS):
    now = datetime.utcnow()
    window_start = now - timedelta(seconds=window_seconds)
    queue = bucket[key]

    while queue and queue[0] < window_start:
        queue.popleft()

    if len(queue) >= max_requests:
        retry_after = window_seconds - int((now - queue[0]).total_seconds())
        if retry_after < 1:
            retry_after = 1
        return True, retry_after

    queue.append(now)
    return False, 0


def is_business_email(email: str):
    email = (email or "").strip().lower()

    if not email:
        return False, "Email is required."

    if not EMAIL_RE.match(email):
        return False, "Enter a valid email address."

    domain = email.split("@", 1)[1]
    if domain in BLOCKED_DOMAINS:
        return False, "Use a business or organization email address."

    return True, ""


def generate_otp():
    return f"{random.randint(100000, 999999)}"


import requests

def send_infobip_email(to_email: str, otp: str):
    url = f"https://555q4d.api.infobip.com/email/4/messages"

    payload = {
        "messages": [
            {
                "destinations": [
                    {
                        "to": [
                            {
                                "destination": to_email
                            }
                        ]
                    }
                ],
                "sender": INFOBIP_SENDER,
                "content": {
                    "subject": "Your verification code",
                    "text": f"Your verification code is: {otp}\n\n"
                    "This code is valid for 120 seconds.\n\n"
                    "If you did not request this code, please ignore this email."
                }
            }
        ]
    }

    headers = {
        "Authorization": f"App {INFOBIP_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)

    print("INFOBIP STATUS:", response.status_code)
    print("INFOBIP BODY:", response.text)

    return response.status_code, response.text


@app.get("/")
def index():
    return send_from_directory("static", "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/send-otp")
@app.post("/backend/send-otp")
def send_otp():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()

    valid, message = is_business_email(email)
    if not valid:
        return jsonify({"error": message}), 400

    client_ip = get_client_ip()

    limited_by_email, retry_email = is_rate_limited(email_rate_limits, email)
    if limited_by_email:
        return jsonify({
            "error": "Too many requests for this email. Please try again shortly.",
            "retry_after": retry_email
        }), 429

    limited_by_ip, retry_ip = is_rate_limited(ip_rate_limits, client_ip)
    if limited_by_ip:
        return jsonify({
            "error": "Too many requests from this IP. Please try again shortly.",
            "retry_after": retry_ip
        }), 429

    if not INFOBIP_API_KEY:
        return jsonify({"error": "Infobip API key is missing."}), 500

    otp = generate_otp()
    expires_at = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)

    status_code, provider_body = send_infobip_email(email, otp)

    if status_code < 200 or status_code >= 300:
        return jsonify({
            "error": "Infobip rejected the request.",
            "provider_status": status_code,
            "provider_body": provider_body
        }), 500

    otp_store[email] = {
        "otp": otp,
        "expires_at": expires_at.isoformat()
    }

    return jsonify({
        "success": True,
        "message": "Code sent successfully.",
        "email": email,
        "expires_in": OTP_EXPIRY_SECONDS
    })


@app.post("/verify-otp")
@app.post("/backend/verify-otp")
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()
    otp = str(data.get("otp", "")).strip()

    record = otp_store.get(email)
    if not record:
        return jsonify({"error": "No active code for this email."}), 400

    expires_at = datetime.fromisoformat(record["expires_at"])
    if datetime.utcnow() > expires_at:
        return jsonify({"error": "OTP expired."}), 400

    if otp != record["otp"]:
        return jsonify({"error": "Invalid OTP."}), 400

    return jsonify({
        "success": True,
        "message": "Verification successful."
    })


@app.post("/resend-otp")
@app.post("/backend/resend-otp")
def resend_otp():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).strip().lower()

    valid, message = is_business_email(email)
    if not valid:
        return jsonify({"error": message}), 400

    record = otp_store.get(email)

    if record:
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.utcnow() <= expires_at:
            otp = record["otp"]
            remaining = int((expires_at - datetime.utcnow()).total_seconds())
        else:
            otp = generate_otp()
            expires_at = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)
            remaining = OTP_EXPIRY_SECONDS
            otp_store[email] = {
                "otp": otp,
                "expires_at": expires_at.isoformat()
            }
    else:
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(seconds=OTP_EXPIRY_SECONDS)
        remaining = OTP_EXPIRY_SECONDS
        otp_store[email] = {
            "otp": otp,
            "expires_at": expires_at.isoformat()
        }

    status_code, provider_body = send_infobip_email(email, otp)

    if status_code < 200 or status_code >= 300:
        return jsonify({
            "error": "Infobip rejected the request.",
            "provider_status": status_code,
            "provider_body": provider_body
        }), 500

    return jsonify({
        "success": True,
        "message": "Code resent successfully.",
        "email": email,
        "expires_in": remaining
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

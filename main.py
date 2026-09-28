from flask import Flask, jsonify, request
from flask_caching import Cache
from response import process_token
from colorama import init, Fore
import warnings
from urllib3.exceptions import InsecureRequestWarning
import time

# Ignore SSL warnings
warnings.filterwarnings("ignore", category=InsecureRequestWarning)

# Initialize colorama
init(autoreset=True)

# Initialize Flask app
app = Flask(__name__)
cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})

# ---------- RETRY CONFIG (VERCEL — 10s timeout) ----------
MAX_RETRIES = 2          # Vercel pe max 2 attempts hi ho sakte hain
RETRY_DELAY = 1.0        # 1 second wait
# ---------------------------------------------------------


def is_token_valid(resp):
    """Check karo response me valid token mila ya nahi."""
    if not isinstance(resp, dict):
        return False
    if resp.get("error"):
        return False
    token = resp.get("token")
    if not token or token in ("N/A", "None", ""):
        return False
    return True


def is_retryable_error(resp):
    """Permanent error pe retry mat karo."""
    if not isinstance(resp, dict):
        return True

    err = str(resp.get("error", "")).lower()

    permanent_errors = [
        "missing open_id",
        "missing access_token",
        "failed to retrieve oauth",
        "invalid credentials",
        "bad json",
        "account banned",
        "wrong password",
    ]

    for p in permanent_errors:
        if p in err:
            return False
    return True


def process_token_with_retry(uid, password, max_retries=MAX_RETRIES):
    """2 baar try karega (Vercel safe)."""
    last_response = None

    for attempt in range(1, max_retries + 1):
        print(Fore.CYAN + f"[RETRY] Attempt {attempt}/{max_retries} for UID {uid}")

        try:
            response = process_token(uid, password)
        except Exception as e:
            print(Fore.RED + f"[RETRY] Exception: {e}")
            response = {"uid": uid, "error": f"Exception: {e}"}

        last_response = response

        # Success
        if is_token_valid(response):
            print(Fore.GREEN + f"[RETRY] [OK] Token mila attempt {attempt} par!")
            return response

        err = response.get("error", "Unknown") if isinstance(response, dict) else "Unknown"
        print(Fore.YELLOW + f"[RETRY] Attempt {attempt} fail: {err}")

        # Permanent error — retry band
        if not is_retryable_error(response):
            print(Fore.RED + "[RETRY] Permanent error — retry band.")
            return response

        if attempt < max_retries:
            time.sleep(RETRY_DELAY)

    print(Fore.RED + f"[RETRY] Saare {max_retries} attempts fail.")
    return last_response if last_response else {"uid": uid, "error": "All retries failed"}


@app.route("/")
def home():
    return "Jwt Token Generator API is running!"


@app.route("/token", methods=["GET"])
def get_responses():
    uid = request.args.get("uid")
    password = request.args.get("password")

    if uid and password:
        response = process_token_with_retry(uid, password)

        cache_key = f"token_{uid}_{password}_{int(time.time())}"
        cache.set(cache_key, response, timeout=25200)  # 7 hours

        return jsonify(response)

    return jsonify({"message": "Bulk retrieval logic has been removed."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

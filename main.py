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

cache = Cache(app, config={"CACHE_TYPE": "SimpleCache"})  # In-memory cache

# ---------- RETRY CONFIG ----------
MAX_RETRIES = 5          # Kitni baar try karega
RETRY_DELAY = 1.0        # Har retry ke beech wait (seconds)
# -----------------------------------


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


def process_token_with_retry(uid, password, max_retries=MAX_RETRIES):
    """5 baar tak try karega agar token fail ho jaye."""
    last_response = None
    for attempt in range(1, max_retries + 1):
        print(Fore.CYAN + f"[RETRY] Attempt {attempt}/{max_retries} for UID {uid}")
        try:
            response = process_token(uid, password)
        except Exception as e:
            print(Fore.RED + f"[RETRY] Exception on attempt {attempt}: {e}")
            response = {"uid": uid, "error": f"Exception: {e}"}

        last_response = response

        if is_token_valid(response):
            print(Fore.GREEN + f"[RETRY] [OK] Token mila attempt {attempt} par!")
            return response

        err = response.get("error") if isinstance(response, dict) else "Unknown error"
        print(Fore.YELLOW + f"[RETRY] Attempt {attempt} fail: {err}")

        if attempt < max_retries:
            time.sleep(RETRY_DELAY)

    print(Fore.RED + f"[RETRY] Saare {max_retries} attempts fail ho gaye.")
    return last_response if last_response else {"uid": uid, "error": "All retries failed"}


@app.route("/")
def home():
    return "Jwt Token Generator API is running!"


@app.route("/token", methods=["GET"])
def get_responses():
    uid = request.args.get("uid")
    password = request.args.get("password")

    if uid and password:
        # 5-baar retry wala system
        response = process_token_with_retry(uid, password)

        # Cache key per request
        cache_key = f"token_{uid}_{password}_{int(time.time())}"
        cache.set(cache_key, response, timeout=25200)  # 7 hours

        return jsonify(response)

    return jsonify({"message": "Bulk retrieval logic has been removed."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

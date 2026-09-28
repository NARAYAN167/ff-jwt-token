import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import json
from colorama import Fore

# The key/IV used to encrypt the MajorLogin payload.
# These differ from the ones in settings.py — keep both if you need them.
MAJOR_LOGIN_KEY = b'Yg&tc%DEuh6%Zc^8'
MAJOR_LOGIN_IV = b'6oyZDr22E3ychjM%'


def get_token(password, uid):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    headers = {
        "Host": "ffmconnect.live.gop.garenanow.com",
        "User-Agent": "GarenaMSDK/4.0.42(SM-A136B ;Android 9;en;US;app 1.132.1 2024061806;)",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "Keep-Alive",
    }
    data = {
        "uid": uid,
        "password": password,
        "response_type": "token",
        "client_type": "2",
        "client_secret": "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3",
        "client_id": "100067",
    }
    try:
        response = requests.post(url, headers=headers, data=data, verify=False, timeout=10)
    except requests.RequestException as e:
        print(Fore.RED + f"[gen_token] Request error: {e}")
        return None

    if response.status_code != 200:
        print(Fore.RED + f"Failed to retrieve token for UID {uid}: HTTP {response.status_code} {response.text[:200]}")
        return None

    try:
        return response.json()
    except Exception as e:
        print(Fore.RED + f"[gen_token] Bad JSON: {e} | body={response.text[:200]}")
        return None


def encrypt_message(key, iv, plaintext):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded_message)


def load_tokens(file_path, limit=None):
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
            tokens = list(data.items())
            if limit is not None:
                tokens = tokens[:limit]
            return tokens
    except Exception as e:
        print(Fore.RED + f"Failed to load tokens: {e}")
        return []
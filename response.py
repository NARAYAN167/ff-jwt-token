import requests
import output_pb2
import login_pb2
from gen_token import encrypt_message, get_token
from settings import AES_KEY, AES_IV
from Crypto.Cipher import AES


def parse_response(response_content):
    """Parse text-format protobuf output into a dict."""
    response_dict = {}
    for line in response_content.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            response_dict[key.strip()] = value.strip().strip('"')
    return response_dict


def decrypt_response(key, iv, ciphertext):
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(ciphertext)
        pad_len = decrypted[-1]
        if 1 <= pad_len <= 16:
            decrypted = decrypted[:-pad_len]
        return decrypted
    except Exception as e:
        print(f"[DEBUG] Decrypt failed: {e}")
        return None


def find_protobuf_offset(data, max_scan=200):
    """Scan response for a valid protobuf offset."""
    best = None
    for offset in range(0, min(len(data), max_scan)):
        try:
            msg = output_pb2.Lokesh()
            msg.ParseFromString(data[offset:])
            if 0 < len(msg.region) < 10 and msg.region.isalpha():
                score = (
                    len(msg.region)
                    + len(msg.place)
                    + (1 if msg.token else 0)
                    + (1 if msg.account_id else 0)
                )
                if best is None or score > best[0]:
                    best = (score, offset, msg)
        except Exception:
            continue
    if best:
        return best[1], best[2]
    return None, None


def _post_login(url, payload, headers):
    """POST the encrypted LoginReq. Returns (ok, response)."""
    try:
        response = requests.post(
            url, data=payload, headers=headers, verify=False, timeout=15
        )
        return True, response
    except requests.RequestException as e:
        print(f"[DEBUG] Request exception: {e}")
        return False, e


def process_token(uid, password):
    # ------------------------------------------------------------------
    # STEP 1: OAuth guest token
    # ------------------------------------------------------------------
    token_data = get_token(password, uid)
    if not token_data:
        return {"uid": uid, "error": "Failed to retrieve OAuth token"}

    print(f"[DEBUG] token_data keys: {list(token_data.keys())}")

    open_id = token_data.get("open_id", "")
    access_token = token_data.get("access_token", "")

    if not open_id or not access_token:
        return {
            "uid": uid,
            "error": "OAuth response missing open_id or access_token",
            "raw": token_data,
        }

    # ------------------------------------------------------------------
    # STEP 2: Build LoginReq (this is what /MajorLogin expects)
    # ------------------------------------------------------------------
    login_req = login_pb2.LoginReq()
    login_req.open_id = open_id
    login_req.open_id_type = "4"           # 4 = guest
    login_req.login_token = access_token
    login_req.orign_platform_type = "4"

    # ------------------------------------------------------------------
    # STEP 3: POST with platform fallback
    # ------------------------------------------------------------------
    url = "https://loginbp.ppmainecoonghj.com/MajorLogin"

    base_headers = {
        "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
        "Accept": "*/*",
        "Accept-Encoding": "deflate, gzip",
        "X-Ga-Sv": "1789534056",
        "Authorization": "Bearer",
        "X-Ga": "v1 1",
        "Releaseversion": "OB55",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Unity-Version": "2018.4.12f1",
    }

    # Guest accounts use "4" as origin platform type
    platform_candidates = ["4", "1", "2", "3", "5", "6", "7", "8", "9"]

    last_response = None

    for plat in platform_candidates:
        login_req.orign_platform_type = plat
        serialized = login_req.SerializeToString()
        encrypted = encrypt_message(AES_KEY, AES_IV, serialized)
        payload = bytes(encrypted)

        print(f"[DEBUG] Trying orign_platform_type={plat!r} | "
              f"payload={len(payload)} bytes")

        ok, response = _post_login(url, payload, base_headers)
        if not ok:
            return {"uid": uid, "error": f"Request failed: {response}"}

        last_response = response

        if response.status_code == 200:
            print(f"[DEBUG] [OK] Platform {plat!r} accepted")
            break

        body_snippet = response.content[:200]
        print(f"[DEBUG] HTTP {response.status_code} | body={body_snippet!r}")

        # If it's a platform error, keep trying. Otherwise stop.
        if b"INVALID_PLATFORM" not in response.content:
            return {
                "uid": uid,
                "error": f"HTTP {response.status_code} {response.reason}",
                "response_body": response.text[:512],
            }
    else:
        # Exhausted all candidates
        return {
            "uid": uid,
            "error": "All platform candidates rejected",
            "last_response": last_response.text[:512] if last_response else None,
        }

    # ------------------------------------------------------------------
    # STEP 4: Parse success response
    # ------------------------------------------------------------------
    raw = last_response.content
    print(f"[DEBUG] Response length: {len(raw)} bytes")

    # Strategy 1: direct parse
    example_msg = output_pb2.Lokesh()
    try:
        example_msg.ParseFromString(raw)
        if example_msg.region and len(example_msg.region) < 10:
            print("[DEBUG] [OK] Direct parse worked")
            return _build_result(uid, parse_response(str(example_msg)), access_token)
    except Exception:
        pass

    # Strategy 2: offset scan
    print("[DEBUG] Scanning for protobuf offset...")
    offset, msg = find_protobuf_offset(raw)
    if offset is not None:
        print(f"[DEBUG] [OK] Found protobuf at offset {offset}")
        print(f"[DEBUG]   region={msg.region}, place={msg.place}")
        return _build_result(uid, parse_response(str(msg)), access_token)

    # Strategy 3: AES decrypt then parse
    print("[DEBUG] Trying AES decrypt...")
    decrypted = decrypt_response(AES_KEY, AES_IV, raw)
    if decrypted:
        offset, msg = find_protobuf_offset(decrypted)
        if offset is not None:
            print(f"[DEBUG] [OK] Decrypt + offset {offset} worked")
            return _build_result(uid, parse_response(str(msg)), access_token)

    return {
        "uid": uid,
        "error": "Failed to deserialize the response",
        "raw_hex": raw.hex()[:512],
    }


def _build_result(uid, response_dict, access_token):
    return {
        "region": response_dict.get("region", "N/A"),
        "status": response_dict.get("status", "N/A"),
        "developer": "@Narayanverma123",
        "token": response_dict.get("token", "N/A"),
        "token_access": access_token,
        "uid": uid,
    }
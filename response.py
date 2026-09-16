import requests
import my_pb2
import output_pb2
from gen_token import encrypt_message, get_token
from settings import AES_KEY, AES_IV
import binascii
from datetime import datetime, timezone
from Crypto.Cipher import AES


def parse_response(response_content):
    response_dict = {}
    lines = response_content.split("\n")
    for line in lines:
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
    """
    Response এর সব offset scan করে valid protobuf খুঁজে বের করে।
    """
    best = None
    for offset in range(0, min(len(data), max_scan)):
        try:
            msg = output_pb2.Lokesh()
            msg.ParseFromString(data[offset:])
            # Validate: region is short alpha string (e.g. "BD", "ME")
            if 0 < len(msg.region) < 10 and msg.region.isalpha():
                score = len(msg.region) + len(msg.place) + (1 if msg.token else 0) + (1 if msg.account_id else 0)
                if best is None or score > best[0]:
                    best = (score, offset, msg)
        except Exception:
            continue
    if best:
        return best[1], best[2]
    return None, None


def process_token(uid, password):
    token_data = get_token(password, uid)
    if not token_data:
        return {"uid": uid, "error": "Failed to retrieve token"}

    def current_timestamp(fmt="iso", tz=timezone.utc):
        now = datetime.now(tz)
        if fmt == "iso":
            return now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if fmt == "epoch":
            return int(now.timestamp())
        return now.strftime(fmt)

    game_data = my_pb2.GameData()
    game_data.timestamp = current_timestamp()
    game_data.game_name = "free fire"
    game_data.game_version = 1
    game_data.version_code = "1.132.1"
    game_data.os_info = "Android OS 11 / API-30 (RKQ1.201112.002/eng.realme.20221110.193122)"
    game_data.device_type = "Handheld"
    game_data.network_provider = "JIO"
    game_data.connection_type = "MOBILE"
    game_data.screen_width = 720
    game_data.screen_height = 1600
    game_data.dpi = "280"
    game_data.cpu_info = "ARM Cortex-A73 | 2200 | 4"
    game_data.total_ram = 4096
    game_data.gpu_name = "Adreno (TM) 610"
    game_data.gpu_version = "OpenGL ES 3.2"
    game_data.user_id = "Google|c71ff1e2-457f-4e2d-83a1-c519fa3f2a44"
    game_data.ip_address = "182.75.115.22"
    game_data.language = "en"
    open_id_value = token_data.get("open_id")
    if not open_id_value:
        open_id_value = f"Google|{uid}"
    game_data.open_id = open_id_value
    game_data.access_token = token_data.get("access_token", "")
    game_data.platform_type = 4
    game_data.device_form_factor = "Handheld"
    game_data.device_model = "realme RMX1825"
    game_data.field_60 = 30000
    game_data.field_61 = 27500
    game_data.field_62 = 1940
    game_data.field_63 = 720
    game_data.field_64 = 28000
    game_data.field_65 = 30000
    game_data.field_66 = 28000
    game_data.field_67 = 30000
    game_data.field_70 = 4
    game_data.field_73 = 2
    game_data.library_path = "/data/app/com.dts.freefireth-fpXCSphIV6dKC7jL-WOyRA==/lib/arm"
    game_data.field_76 = 1
    game_data.apk_info = "e62ab9354d8fb5fb081db338acb33491|/data/app/com.dts.freefireth-fpXCSphIV6dKC7jL-WOyRA==/base.apk"
    game_data.field_78 = 6
    game_data.field_79 = 1
    game_data.os_architecture = "64"
    game_data.build_number = "2024061806"
    game_data.field_85 = 1
    game_data.graphics_backend = "OpenGLES3"
    game_data.max_texture_units = 16383
    game_data.rendering_api = 4
    game_data.encoded_field_89 = "\x10U\x15\x03\x02\t\rPYN\tEX\x03AZO9X\x07\rU\niZPVj\x05\rm\t\x04c"
    game_data.field_92 = 8999
    game_data.marketplace = "3rd_party"
    game_data.encryption_key = "Jp2DT7F3Is55K/92LSJ4PWkJxZnMzSNn+HEBK2AFBDBdrLpWTA3bZjtbU3JbXigkIFFJ5ZJKi0fpnlJCPDD2A7h2aPQ="
    game_data.total_storage = 64000
    game_data.field_97 = 1
    game_data.field_98 = 1
    game_data.field_99 = "4"
    game_data.field_100 = b"4"

    serialized_data = game_data.SerializeToString()
    encrypted_data = encrypt_message(AES_KEY, AES_IV, serialized_data)
    hex_encrypted_data = binascii.hexlify(encrypted_data).decode("utf-8")

    # ✅ NEW URL (already correct)
    url = "https://loginbp.ppmainecoonghj.com/MajorLogin"

    headers = {
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

    edata = bytes.fromhex(hex_encrypted_data)

    try:
        response = requests.post(
            url, data=edata, headers=headers, verify=False, timeout=15,
        )

        if response.status_code != 200:
            print(f"[DEBUG] HTTP {response.status_code} | {response.reason}")
            return {
                "uid": uid,
                "error": f"Failed to get response: HTTP {response.status_code}, {response.reason}",
            }

        raw = response.content
        print(f"[DEBUG] Response length: {len(raw)} bytes")

        # ==========================================
        # STRATEGY 1: Direct parse
        # ==========================================
        example_msg = output_pb2.Lokesh()
        try:
            example_msg.ParseFromString(raw)
            if example_msg.region and len(example_msg.region) < 10:
                print("[DEBUG] ✅ Direct parse worked")
                response_dict = parse_response(str(example_msg))
                return _build_result(uid, response_dict, game_data)
        except Exception:
            pass

        # ==========================================
        # STRATEGY 2: Find protobuf offset (main fix)
        # ==========================================
        print("[DEBUG] Scanning for protobuf offset...")
        offset, msg = find_protobuf_offset(raw)
        if offset is not None:
            print(f"[DEBUG] ✅ Found protobuf at offset {offset}")
            print(f"[DEBUG]   region={msg.region}, place={msg.place}")
            response_dict = parse_response(str(msg))
            return _build_result(uid, response_dict, game_data)

        # ==========================================
        # STRATEGY 3: AES decrypt
        # ==========================================
        print("[DEBUG] Trying AES decrypt...")
        decrypted = decrypt_response(AES_KEY, AES_IV, raw)
        if decrypted:
            offset, msg = find_protobuf_offset(decrypted)
            if offset is not None:
                print(f"[DEBUG] ✅ Decrypt + offset {offset} worked")
                response_dict = parse_response(str(msg))
                return _build_result(uid, response_dict, game_data)

        return {
            "uid": uid,
            "error": "Failed to deserialize the response",
            "raw_hex": raw.hex(),
        }

    except requests.RequestException as e:
        return {
            "uid": uid,
            "error": f"An error occurred while making the request: {e}",
        }


def _build_result(uid, response_dict, game_data):
    return {
        "region": response_dict.get("region", "N/A"),
        "status": response_dict.get("status", "N/A"),
        "credit": "@Narayanverma123",
        "token": response_dict.get("token", "N/A"),
        "token_access": game_data.access_token,
        "uid": uid,
    }

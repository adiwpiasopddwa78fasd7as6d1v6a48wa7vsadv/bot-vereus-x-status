import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask

# =======================================================
# CONFIGURATION (ตั้งค่าตรงนี้)
# =======================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1514211987234488401/dT70YrRMx2yVHSfw_Cb6Opf6VqdY8W5nOw5RQSU-qNLoGHO7ZPM5JQsH3Pfj9ei_LgYO"   # <-- ใส่ webhook ใหม่ตรงนี้ (อย่าแชร์ออกไปอีก)
EXPLOIT_API_URL = "https://weao.xyz/api/status/exploits"
VERSION_API_URL = "https://weao.xyz/api/versions/current"
CHECK_INTERVAL = 60          # แนะนำ >= 60 วิ กัน rate limit (429)
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ── รายชื่อตายตัวตามหมวดหมู่ที่กำหนด ──────────────────────────
CATEGORY_LISTS = {
    "Windows Script Executor Exploits": [
        "Volt", "Potassium", "Wave", "Synapse Z", "Seliware",
        "Madium", "Cosmic", "Velocity", "SirHurt", "Solara", "Xeno"
    ],
    "Mac Script Executor Exploits": [
        "MacSploit", "Opiumware"
    ],
    "Android Script Executor Exploits": [
        "Delta", "Vega X", "Codex"
    ],
    "iOS Script Executor Exploits": [
        "Delta"
    ],
    "Windows External Exploits": [
        "Serotonin", "Severe", "RbxCli", "Lumen", "Matcha",
        "Matrix Hub", "Photon", "DX9WARE V2"
    ],
}

# Platform ที่ใช้กรองคู่กับชื่อ กันชื่อซ้ำข้ามแพลตฟอร์ม (เช่น Delta มีทั้ง Android/iOS)
CATEGORY_PLATFORM = {
    "Windows Script Executor Exploits": "Windows",
    "Mac Script Executor Exploits": "Mac",
    "Android Script Executor Exploits": "Android",
    "iOS Script Executor Exploits": "iOS",
    "Windows External Exploits": "Windows",
}

# ── ดึงสถานะ exploit ──────────────────────────────────────────
def fetch_exploit_data():
    headers = {"User-Agent": "WEAO-3PService"}
    try:
        resp = requests.get(EXPLOIT_API_URL, headers=headers, timeout=15)
        if resp.status_code == 429:
            print(f"[{time.strftime('%X')}] โดน Rate Limit จาก WEAO Exploit API")
            return "RATELIMIT", []
        if resp.status_code != 200:
            print(f"[{time.strftime('%X')}] WEAO Exploit API ตอบกลับ status {resp.status_code}")
            return "OFFLINE", []
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("exploits") or data.get("data") or []
        return "ONLINE", data
    except Exception as e:
        print(f"[{time.strftime('%X')}] บอทเกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return "OFFLINE", []

# ── ดึงเวอร์ชัน Roblox ปัจจุบัน ─────────────────────────────────
def fetch_roblox_versions():
    headers = {"User-Agent": "WEAO-3PService"}
    try:
        resp = requests.get(VERSION_API_URL, headers=headers, timeout=15)
        if resp.status_code != 200:
            print(f"[{time.strftime('%X')}] WEAO Version API ตอบกลับ status {resp.status_code}")
            return None
        return resp.json()
    except Exception as e:
        print(f"[{time.strftime('%X')}] ดึงข้อมูล Roblox Version ผิดพลาด: {e}")
        return None

def get_status_text(ex):
    """
    สถานะมีแค่ 3 แบบ:
    🟢 Working  -> updateStatus = True และไม่มี hasIssues
    🟠 Issues   -> updateStatus = True แต่ hasIssues = True
    🔴 Patched  -> updateStatus = False
    """
    update_ok  = ex.get("updateStatus", False)
    has_issues = ex.get("hasIssues", False)

    if not update_ok:
        return "🔴 Patched"
    if has_issues:
        return "🟠 Issues"
    return "🟢 Working"

def categorize_executors(exploits):
    categorized = {cat: [] for cat in CATEGORY_LISTS}
    lookup = {}
    for ex in exploits:
        key = (ex.get("title", ""), ex.get("platform", ""))
        lookup[key] = ex

    for category, names in CATEGORY_LISTS.items():
        platform = CATEGORY_PLATFORM[category]
        for name in names:
            ex = lookup.get((name, platform))
            if ex:
                status_str = get_status_text(ex)
                categorized[category].append(f"**{name}** : {status_str}")
            else:
                categorized[category].append(f"**{name}** : ⚪ Not Found")

    return categorized

# ── สร้าง field หมวด Roblox Version ─────────────────────────────
def build_version_field(versions):
    if not versions:
        value_text = "*Unable to fetch version data*"
        return {"name": "🧩 Roblox Version Update Tracker", "value": value_text, "inline": False}

    win_ver  = versions.get("Windows", "Unknown")
    win_date = versions.get("WindowsDate", "")
    mac_ver  = versions.get("Mac", "Unknown")
    mac_date = versions.get("MacDate", "")
    and_ver  = versions.get("Android", "Unknown")
    and_date = versions.get("AndroidDate", "")
    ios_ver  = versions.get("iOS", "Unknown")
    ios_date = versions.get("iOSDate", "")

    lines = [
        f"**Roblox Windows** : `{win_ver}`\n└ Last Updated: {win_date}",
        f"**Roblox Mac** : `{mac_ver}`\n└ Last Updated: {mac_date}",
        f"**Roblox Android-iOS** : `Android {and_ver}` / `iOS {ios_ver}`\n└ Android: {and_date}\n└ iOS: {ios_date}",
    ]
    value_text = "\n\n".join(lines)

    return {"name": "🧩 Roblox Version Update Tracker", "value": value_text, "inline": False}

def build_embed(api_status, categories, versions):
    fields = []

    # ── หมวด Roblox Version ขึ้นก่อนเป็นอันดับแรก ──
    fields.append(build_version_field(versions))

    # ── หมวด Exploit ตามเดิม ──
    for category, items in categories.items():
        value_text = "\n".join(items) if items else "*No data in this category*"
        if len(value_text) > 1024:
            value_text = value_text[:1000] + "\n...(truncated)"
        fields.append({"name": f"💻 {category}", "value": value_text, "inline": False})

    if api_status == "ONLINE":
        embed_color = 65280
        status_label = "🟢 ONLINE"
    elif api_status == "RATELIMIT":
        embed_color = 16776960
        status_label = "🟡 RATE LIMITED"
    else:
        embed_color = 16711680
        status_label = "🔴 OFFLINE"

    current_time_str = time.strftime('%X')

    payload = {
        "embeds": [
            {
                "title": "🛡️ WEAO Status by siw",
                "description": (
                    f"**🌐 WEBSITE WEAO STATUS:** {status_label}\n\n"
                    f"🟢 Working = UPDATE  |  🟠 Issues = WAITING FIX  |  🔴 Patched = DOWN"
                ),
                "color": embed_color,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": f"{FOOTER_TEXT} | Last Updated: {current_time_str}"}
            }
        ]
    }
    return payload

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")
    time.sleep(3)
    print("=== ระบบดึงข้อมูล Exploit + Roblox Version จาก WEAO API เริ่มทำงาน ===")

    while True:
        api_status, exploits = fetch_exploit_data()
        versions = fetch_roblox_versions()

        categories = categorize_executors(exploits) if exploits else {cat: [] for cat in CATEGORY_LISTS}
        payload = build_embed(api_status, categories, versions)

        try:
            if message_id is None:
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] สร้างข้อความหลักสำเร็จ (ID: {message_id})")
                else:
                    print(f"[{time.strftime('%X')}] ส่ง Webhook ไม่สำเร็จ: {response.status_code} - {response.text}")
            else:
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตสถานะเรียบร้อย ({api_status})")
                elif response.status_code == 404:
                    message_id = None
                else:
                    print(f"[{time.strftime('%X')}] แก้ไขข้อความไม่สำเร็จ: {response.status_code}")
        except Exception as e:
            print(f"Discord Webhook Error: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()

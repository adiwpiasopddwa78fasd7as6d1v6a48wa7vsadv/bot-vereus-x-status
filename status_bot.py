import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask

# =======================================================
# CONFIGURATION (ตั้งค่าตรงนี้)
# =======================================================
WEBHOOK_URL = "https://discord.com/api/webhooks/1514211987234488401/dT70YrRMx2yVHSfw_Cb6Opf6VqdY8W5nOw5RQSU-qNLoGHO7ZPM5JQsH3Pfj9ei_LgYO"
API_URL = "https://weao.xyz/api/status/exploits"
CHECK_INTERVAL = 60          # แนะนำ >= 60 วิ กัน rate limit (429)
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v6 is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_exploit_data():
    """ดึงข้อมูล exploit จาก WEAO API จริง"""
    headers = {"User-Agent": "WEAO-3PService"}
    try:
        resp = requests.get(API_URL, headers=headers, timeout=15)
        if resp.status_code == 429:
            print(f"[{time.strftime('%X')}] โดน Rate Limit จาก WEAO API")
            return "RATELIMIT", []
        if resp.status_code != 200:
            print(f"[{time.strftime('%X')}] WEAO API ตอบกลับ status {resp.status_code}")
            return "OFFLINE", []
        data = resp.json()
        if isinstance(data, dict):
            data = data.get("exploits") or data.get("data") or []
        return "ONLINE", data
    except Exception as e:
        print(f"[{time.strftime('%X')}] บอทเกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return "OFFLINE", []

def categorize_executors(exploits):
    """
    แบ่งกลุ่มตาม platform จริง + extype
    หมายเหตุสำคัญ: API ไม่มี platform "External" จริงๆ
    - ตัวที่เป็น Windows + extype="wexternal" คือ External Windows executor
    - ตัวอื่นๆ จัดตาม platform ปกติ (Windows internal, Mac, Android, iOS)
    """
    categorized = {
        "Windows (Internal)": [],
        "Windows (External)": [],
        "Mac": [],
        "Android": [],
        "iOS": [],
    }

    for ex in exploits:
        title     = ex.get("title", "Unknown")
        platform  = (ex.get("platform") or "").strip()
        extype    = (ex.get("extype") or "").lower()
        update_ok = ex.get("updateStatus", False)
        detected  = ex.get("detected", False)

        # ── สถานะหลัก: ใช้ updateStatus เป็นตัวตัดสิน "ใช้งานได้ไหมตอนนี้" ──
        if update_ok:
            status_str = "🟢 Working"
        else:
            status_str = "🔴 Patched"

        # ── detected เป็นแค่ info เสริม ไม่ใช่สถานะหลัก ──
        # (detected:true หมายถึง "เคยโดนตรวจจับ/มีประวัติแบน" ไม่ใช่ "กำลังโดนอยู่ตอนนี้")
        if detected:
            status_str += " ⚠️"

        entry = f"**{title}** : {status_str}"

        # ── จัดกลุ่มตาม platform + extype จริง ──
        if platform == "Windows":
            if extype == "wexternal":
                categorized["Windows (External)"].append(entry)
            else:
                categorized["Windows (Internal)"].append(entry)
        elif platform == "Mac":
            categorized["Mac"].append(entry)
        elif platform == "Android":
            categorized["Android"].append(entry)
        elif platform == "iOS":
            categorized["iOS"].append(entry)

    return categorized

def build_embed(api_status, categories):
    fields = []
    for platform, items in categories.items():
        value_text = "\n".join(items) if items else "*ไม่มีข้อมูลตัวรันในกลุ่มนี้*"
        if len(value_text) > 1024:
            value_text = value_text[:1000] + "\n...(ตัดทอน)"
        fields.append({"name": f"💻 {platform}", "value": value_text, "inline": False})

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
                "title": "🛡️ Executor Status by siw",
                "description": (
                    f"**🌐 สถานะ WEAO API:** {status_label}\n\n"
                    f"🟢 Working = อัปเดตล่าสุดแล้ว / 🔴 Patched = ยังไม่อัปเดต\n"
                    f"⚠️ = เคยมีประวัติโดนตรวจจับ/แบนมาก่อน (ไม่ได้แปลว่ากำลังโดนตอนนี้)"
                ),
                "color": embed_color,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": f"{FOOTER_TEXT} | อัปเดตล่าสุด: {current_time_str}"}
            }
        ]
    }
    return payload

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")
    time.sleep(3)
    print("=== ระบบดึงข้อมูลตรงจาก WEAO API เริ่มทำงาน ===")

    while True:
        api_status, exploits = fetch_exploit_data()
        categories = categorize_executors(exploits) if exploits else {
            "Windows (Internal)": [], "Windows (External)": [],
            "Mac": [], "Android": [], "iOS": []
        }
        payload = build_embed(api_status, categories)

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

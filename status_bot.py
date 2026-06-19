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
    return "<h1>Vereus X Status System v5 is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_exploit_data():
    """ดึงข้อมูล exploit จาก WEAO API จริง (ไม่ใช่ scrape HTML)"""
    headers = {
        # จำเป็นต้องมี ไม่งั้นโดนบล็อก
        "User-Agent": "WEAO-3PService"
    }
    try:
        resp = requests.get(API_URL, headers=headers, timeout=15)
        if resp.status_code == 429:
            print(f"[{time.strftime('%X')}] โดน Rate Limit จาก WEAO API")
            return "RATELIMIT", []
        if resp.status_code != 200:
            print(f"[{time.strftime('%X')}] WEAO API ตอบกลับ status {resp.status_code}")
            return "OFFLINE", []
        data = resp.json()
        # บางครั้ง API คืน list ตรงๆ บางครั้งห่อใน key เช่น "exploits"
        if isinstance(data, dict):
            data = data.get("exploits") or data.get("data") or []
        return "ONLINE", data
    except Exception as e:
        print(f"[{time.strftime('%X')}] บอทเกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return "OFFLINE", []

def categorize_executors(exploits):
    """แบ่งกลุ่มตาม platform จาก field จริงของ API"""
    categorized = {
        "Windows": [],
        "Mac": [],
        "Android": [],
        "iOS": [],
        "External": []
    }

    for ex in exploits:
        title       = ex.get("title", "Unknown")
        platform    = (ex.get("platform") or "").strip()
        extype      = (ex.get("extype") or "").lower()
        update_ok   = ex.get("updateStatus", False)
        detected    = ex.get("detected", True)

        # สถานะ: ต้อง updateStatus=True และ detected=False ถึงจะนับว่า Working
        if update_ok and not detected:
            status_str = "🟢 Working"
        elif update_ok and detected:
            status_str = "🟠 Detected"
        else:
            status_str = "🔴 Patched"

        entry = f"**{title}** : {status_str}"

        # จัดกลุ่มตาม platform field ของจริง (ไม่เดาจาก keyword ใน HTML แล้ว)
        if platform == "Windows":
            categorized["Windows"].append(entry)
        elif platform == "Mac":
            categorized["Mac"].append(entry)
        elif platform == "Android":
            categorized["Android"].append(entry)
        elif platform == "iOS":
            categorized["iOS"].append(entry)
        elif "external" in extype:
            categorized["External"].append(entry)
        else:
            # ไม่เข้าเงื่อนไขไหนเลย ใส่ External เป็นค่าเริ่มต้น
            categorized["External"].append(entry)

    return categorized

def build_embed(api_status, categories):
    fields = []
    for platform, items in categories.items():
        # จำกัดความยาวกัน field เกิน 1024 ตัวอักษรของ Discord
        value_text = "\n".join(items) if items else "*ไม่มีข้อมูลตัวรันในกลุ่มนี้*"
        if len(value_text) > 1024:
            value_text = value_text[:1000] + "\n...(ตัดทอน)"
        fields.append({"name": f"💻 {platform} Executors", "value": value_text, "inline": False})

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
                "description": f"**🌐 สถานะ WEAO API:** {status_label}\n\n"
                               f"ดึงข้อมูลตรงจาก WEAO API แบบ Real-time (api/status/exploits)",
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
            "Windows": [], "Mac": [], "Android": [], "iOS": [], "External": []
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

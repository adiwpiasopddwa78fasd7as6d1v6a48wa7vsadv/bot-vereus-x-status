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
API_URL = "https://weao.xyz/api/status"
CHECK_INTERVAL = 20
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

# 🌐 สร้างหน้าเว็บจำลองเพื่อหลอกระบบตรวจเช็คของ Render ไม่ให้บอทดับ
app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System is Online!</h1>", 200

def keep_alive():
    # ดึงพอร์ตที่ Render กำหนดมาให้ ถ้าไม่มีจะใช้ 8080 เป็นค่าเริ่มต้น
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def get_weao_api_status():
    categorized_executors = {"Windows": [], "Mac": [], "Android": [], "iOS": [], "External": []}
    try:
        response = requests.get(API_URL, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return "OFFLINE", categorized_executors

        data = response.json()
        executors_list = data.get("executors", data) if isinstance(data, dict) else data
        
        if not isinstance(executors_list, list):
            return "ONLINE", categorized_executors

        for item in executors_list:
            if not isinstance(item, dict):
                continue
            name = item.get("name", "Unknown")
            raw_status = str(item.get("status", "")).lower()
            platform = str(item.get("platform", "")).lower() or str(item.get("type", "")).lower()

            if "work" in raw_status or "online" in raw_status or "up" in raw_status:
                status_str = f"🟢 Working"
            elif "patch" in raw_status or "update" in raw_status:
                status_str = f"🟠 Patched"
            else:
                status_str = f"🔴 Down"

            text_line = f"**{name}** : {status_str}"

            if "win" in platform: categorized_executors["Windows"].append(text_line)
            elif "mac" in platform: categorized_executors["Mac"].append(text_line)
            elif "android" in platform or "apk" in platform: categorized_executors["Android"].append(text_line)
            elif "ios" in platform or "apple" in platform: categorized_executors["iOS"].append(text_line)
            elif "external" in platform or "tool" in platform: categorized_executors["External"].append(text_line)
            else: categorized_executors["Windows"].append(text_line)

        return "ONLINE", categorized_executors
    except Exception as e:
        print(f"[{time.strftime('%X')}] Error connecting to API: {e}")
        return "OFFLINE", categorized_executors

def build_embed(web_status, categories):
    fields = []
    for platform, items in categories.items():
        value_text = "\n".join(items) if items else "*ไม่มีข้อมูลตัวรัน หรือเชื่อมต่อเว็บไม่ได้*"
        fields.append({"name": f"💻 {platform} Executors", "value": value_text, "inline": False})

    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%X')

    payload = {
        "embeds": [
            {
                "title": "🛡️ Executor Status by siw",
                "description": f"**🌐 สถานะการเชื่อมต่อ API:** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE'}\n\n"
                               f"ตรวจสอบสถานะตัวรัน Roblox ทุกแพลตฟอร์มแบบอัตโนมัติ",
                "color": embed_color,
                "fields": fields,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {"text": f"{FOOTER_TEXT} | รีเฟรชทุก {CHECK_INTERVAL}ส. (อัปเดตล่าสุด: {current_time_str})"}
            }
        ]
    }
    return payload

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")

    # รอให้เว็บเซิร์ฟเวอร์หลักบูตเสร็จก่อนเริ่มส่ง Webhook
    time.sleep(5)
    print("=== เริ่มทำงานระบบ Multi-Platform Status Monitor ===")

    while True:
        web_status, categories = get_weao_api_status()
        payload = build_embed(web_status, categories)
        try:
            if message_id is None:
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] บูตข้อความเริ่มต้นสำเร็จ! (ID: {message_id})")
            else:
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตสเตตัสแบบ Real-time สำเร็จ")
                elif response.status_code == 404:
                    message_id = None
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    # สั่งเปิดเว็บเซิร์ฟเวอร์หลอก Render เป็นเบื้องหลัง (Background Thread)
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    
    # รันลูปเช็คสถานะบอทหลัก
    monitor_loop()

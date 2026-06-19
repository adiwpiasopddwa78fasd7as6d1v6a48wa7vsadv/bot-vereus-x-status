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
TARGET_URL = "https://weao.xyz"
CHECK_INTERVAL = 25  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System is Running via Advanced Scraping!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def get_weao_scraped_status():
    """ฟังก์ชันขูดข้อมูลหน้าเว็บแบบละเอียด กวาดสเตตัสทั้งหน้าและหลังชื่อตัวรัน"""
    categorized_executors = {
        "Windows": [],
        "Mac": [],
        "Android": [],
        "iOS": [],
        "External": []
    }
    
    # รายชื่อตัวรันแบ่งตามแพลตฟอร์ม (แก้ไข เพิ่ม/ลด ชื่อตรงนี้ได้เลย)
    executors_config = {
        "Windows": ["Wave", "Solara", "Celery", "Lunar", "Electron", "Nihon"],
        "Mac": ["MacSploit"],
        "Android": ["Delta", "Codex", "Arceus X", "Vega X", "Evon", "Fluxus"],
        "iOS": ["Appleware", "Delta iOS", "Codex iOS", "SwiftSploit"],
        "External": ["Celestial", "Horizon"]
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(TARGET_URL, timeout=15, headers=headers)
        
        if response.status_code != 200:
            print(f"[{time.strftime('%X')}] เว็บหลักตอบกลับด้วย Status Code: {response.status_code}")
            return "OFFLINE", categorized_executors

        html_content = response.text.lower()
        
        for platform, names in executors_config.items():
            for name in names:
                name_lower = name.lower()
                
                if name_lower in html_content:
                    start_idx = html_content.find(name_lower)
                    
                    # 🔍 จุดสำคัญ: ดึงเนื้อหาขยายไปทางซ้าย (ก่อนหน้า) และทางขวา (ข้างหลัง) อย่างละ 250 ตัวอักษร
                    left_bound = max(0, start_idx - 250)
                    right_bound = min(len(html_content), start_idx + 250)
                    snippet = html_content[left_bound:right_bound]
                    
                    # ไล่เช็คคีย์เวิร์ดสถานะรอบๆ ตัวชื่อของมัน
                    if "working" in snippet or "online" in snippet or "🟢" in snippet or "updated" in snippet or "safe" in snippet:
                        status_str = "🟢 Working"
                    elif "patched" in snippet or "updating" in snippet or "🟠" in snippet or "unverified" in snippet:
                        status_str = "🟠 Patched"
                    else:
                        status_str = "🔴 Down"
                else:
                    # ถ้าหาชื่อไม่เจอเลยบนเว็บ แปลว่าอาจจะถูกถอดออกชั่วคราวหรือเปลี่ยนชื่อ
                    status_str = "🔴 Down"
                    
                categorized_executors[platform].append(f"**{name}** : {status_str}")
                
        return "ONLINE", categorized_executors

    except Exception as e:
        print(f"[{time.strftime('%X')}] เกิดข้อผิดพลาดในการเชื่อมต่อหน้าเว็บ: {e}")
        return "OFFLINE", categorized_executors

def build_embed(web_status, categories):
    fields = []
    for platform, items in categories.items():
        value_text = "\n".join(items) if items else "*ไม่มีข้อมูลตัวรันในกลุ่มนี้*"
        fields.append({"name": f"💻 {platform} Executors", "value": value_text, "inline": False})

    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%X')

    payload = {
        "embeds": [
            {
                "title": "🛡️ Executor Status by siw",
                "description": f"**🌐 สถานะเว็บไซต์ (weao.xyz):** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE (เว็บล่ม/โดนบล็อก)'}\n\n"
                               f"ตรวจสอบสถานะตัวรัน Roblox ทุกแพลตฟอร์มแบบ Real-time",
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

    time.sleep(5)
    print("=== ระบบสแกนหน้าเว็บเวอร์ชัน 2 (Advanced Scraping) เริ่มทำงาน ===")

    while True:
        web_status, categories = get_weao_scraped_status()
        payload = build_embed(web_status, categories)
        try:
            if message_id is None:
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] ส่งข้อความสเตตัสเริ่มต้นสำเร็จ (ID: {message_id})")
            else:
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตสถานะและแก้ไขข้อความเดิมเรียบร้อย")
                elif response.status_code == 404:
                    message_id = None
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()

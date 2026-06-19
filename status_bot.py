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
    return "<h1>Vereus X Status System v3 is Running Smoothly!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def get_weao_scraped_status():
    """ระบบคัดกรองขั้นสูง: หั่นครึ่งหน้าเว็บแยกตามแพลตฟอร์มเพื่อป้องกันสเตตัสซ้ำซ้อน"""
    categorized_executors = {
        "Windows": [],
        "Mac": [],
        "Android": [],
        "iOS": [],
        "External": []
    }
    
    # คลังรายชื่อตัวรันชุดใหญ่ จัดเต็มครบทุกแพลตฟอร์มอัปเดตล่าสุด
    executors_config = {
        "Windows": ["Wave", "Solara", "Celery", "Lunar", "Electron", "Nihon", "Incognito", "Swift", "Aimmy", "Krampus"],
        "Mac": ["MacSploit", "Hydrogen", "Delta"],
        "Android": ["Delta", "Codex", "Arceus X", "Vega X", "Evon", "Fluxus", "Hydrogen", "Kitten Exploits", "Cryptic", "Cubix"],
        "iOS": ["Appleware", "Delta", "Codex", "SwiftSploit", "Hydrogen", "Flare"],
        "External": ["Celestial", "Horizon", "Phantom", "Bloodhound", "Viper"]
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        response = requests.get(TARGET_URL, timeout=15, headers=headers)
        
        if response.status_code != 200:
            return "OFFLINE", categorized_executors

        html_content = response.text.lower()
        
        # ✂️ ตัดแบ่งโซน HTML ออกเป็นชิ้นๆ ตามแพลตฟอร์ม เพื่อไม่ให้ชื่อซ้ำกันวิ่งไปชนกันเอง
        idx_win = html_content.find("windows")
        idx_mac = html_content.find("mac")
        idx_and = html_content.find("android")
        idx_ios = html_content.find("ios")
        idx_ext = html_content.find("external")
        
        sections = {
            "Windows": html_content[idx_win:idx_mac] if idx_win != -1 and idx_mac != -1 else html_content,
            "Mac": html_content[idx_mac:idx_and] if idx_mac != -1 and idx_and != -1 else html_content,
            "Android": html_content[idx_and:idx_ios] if idx_and != -1 and idx_ios != -1 else html_content,
            "iOS": html_content[idx_ios:idx_ext] if idx_ios != -1 and idx_ext != -1 else html_content,
            "External": html_content[idx_ext:] if idx_ext != -1 else html_content
        }
        
        # ลูปค้นหาแยกตามโซนใครโซนมัน
        for platform, names in executors_config.items():
            zone_html = sections[platform]
            
            for name in names:
                name_lower = name.lower()
                
                if name_lower in zone_html:
                    start_idx = zone_html.find(name_lower)
                    # ดึงเศษโค้ดรอบข้างชื่อตัวรันมาสแกน 400 ตัวอักษร (หน้า 200 หลัง 200)
                    left_bound = max(0, start_idx - 200)
                    right_bound = min(len(zone_html), start_idx + 200)
                    snippet = zone_html[left_bound:right_bound]
                    
                    # 🟢 เช็คคำค้นหา + ดักคลาสสี (Green/Emerald/Lime) ของฝั่งที่ใช้งานได้
                    if any(x in snippet for x in ["working", "online", "updated", "safe", "active", "green", "emerald", "lime", "text-green", "bg-green"]):
                        status_str = "🟢 Working"
                    # 🟠 เช็คคำค้นหา + ดักคลาสสี (Orange/Amber/Yellow) ของฝั่งที่โดนแพตช์/ปรับปรุง
                    elif any(x in snippet for x in ["patched", "updating", "maintenance", "orange", "amber", "yellow", "text-orange", "text-amber"]):
                        status_str = "🟠 Patched"
                    # 🔴 นอกเหนือจากนั้น หรือขึ้นคลาสสีแดง/Rose ตีเป็นล่มทั้งหมด
                    else:
                        status_str = "🔴 Down"
                else:
                    # ถ้าไม่มีชื่อนี้ในโซนแพลตฟอร์มนั้นๆ ให้ขึ้น Down ไว้ก่อน
                    status_str = "🔴 Down"
                    
                categorized_executors[platform].append(f"**{name}** : {status_str}")
                
        return "ONLINE", categorized_executors

    except Exception as e:
        print(f"[{time.strftime('%X')}] เซิร์ฟเวอร์ขูดข้อมูลเกิดข้อผิดพลาด: {e}")
        return "OFFLINE", categorized_executors

def build_embed(web_status, categories):
    fields = []
    for platform, items in categories.items():
        value_text = "\n".join(items) if items else "*กำลังโหลดข้อมูล...*"
        fields.append({"name": f"💻 {platform} Executors", "value": value_text, "inline": False})

    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%X')

    payload = {
        "embeds": [
            {
                "title": "🛡️ Executor Status by siw",
                "description": f"**🌐 สถานะเว็บไซต์ (weao.xyz):** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE'}\n\n"
                               f"ระบบสแกนโค้ดและวิเคราะห์สถานะแบบเจาะลึกแยกแพลตฟอร์ม",
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
    print("=== ระบบสแกนจำแนกโซน (Zone-Scraping Monitor v3) เริ่มทำงาน ===")

    while True:
        web_status, categories = get_weao_scraped_status()
        payload = build_embed(web_status, categories)
        try:
            if message_id is None:
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] สร้างข้อความหลักสำเร็จ (ID: {message_id})")
            else:
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตข้อมูลตรงตามโซนเรียบร้อย")
                elif response.status_code == 404:
                    message_id = None
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()

import time
import requests
from datetime import datetime, timezone
import os
from threading import Thread
from flask import Flask
import re

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
    return "<h1>Vereus X Status System v4 is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def get_weao_scraped_status():
    """ระบบค้นหาอัจฉริยะ V4: เจาะพิกัดรอบชื่อตัวรัน แยกแยะแพลตฟอร์มป้องกันชื่อซ้ำ"""
    categorized_executors = {
        "Windows": [],
        "Mac": [],
        "Android": [],
        "iOS": [],
        "External": []
    }
    
    # รายชื่อตัวรันทั้งหมดบนเว็บ weao.xyz แบ่งกลุ่มชัดเจน
    executors_config = {
        "Windows": ["Wave", "Solara", "Celery", "Lunar", "Electron", "Nihon", "Incognito", "Swift"],
        "Mac": ["MacSploit", "Hydrogen"],
        "Android": ["Delta", "Codex", "Arceus X", "Vega X", "Evon", "Fluxus", "Hydrogen"],
        "iOS": ["Appleware", "Delta", "Codex", "SwiftSploit", "Hydrogen"],
        "External": ["Celestial", "Horizon"]
    }
    
    # คีย์เวิร์ดอ้างอิงเพื่อใช้แยกแยะกรณีชื่อซ้ำกันข้ามแพลตฟอร์ม
    platform_keywords = {
        "Windows": ["windows", "pc", "win"],
        "Mac": ["mac", "macos", "macsploit"],
        "Android": ["android", "apk", "mobile"],
        "iOS": ["ios", "apple", "ipa", "iphone"],
        "External": ["external", "tool", "cheat"]
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5'
        }
        response = requests.get(TARGET_URL, timeout=15, headers=headers)
        
        if response.status_code != 200:
            return "OFFLINE", categorized_executors

        html_content = response.text.lower()
        
        for platform, names in executors_config.items():
            for name in names:
                name_lower = name.lower()
                
                # ค้นหาตำแหน่งทั้งหมดของชื่อนี้ในหน้าเว็บ (เช่น หาคำว่า Delta ทั้งหมดที่โผล่มา)
                indices = [m.start() for m in re.finditer(re.escape(name_lower), html_content)]
                
                if not indices:
                    # ถ้าไม่มีชื่อนี้อยู่บนหน้าเว็บเลย
                    categorized_executors[platform].append(f"**{name}** : 🔴 Down")
                    continue
                
                # คัดเลือกก้อนเนื้อหา HTML ที่ถูกต้องตามแพลตฟอร์มของมัน
                chosen_snippet = ""
                for idx in indices:
                    left_bound = max(0, idx - 300)
                    right_bound = min(len(html_content), idx + 300)
                    current_snippet = html_content[left_bound:right_bound]
                    
                    # เช็คว่าก้อน HTML รอบๆ ชื่อนี้ มีคำระบุแพลตฟอร์มของมันอยู่ด้วยไหม
                    if any(kp in current_snippet for kp in platform_keywords[platform]):
                        chosen_snippet = current_snippet
                        break
                
                # ค่าเริ่มต้นหากไม่พบก้อนที่ตรงกับแพลตฟอร์ม ให้ดึงก้อนแรกสุดมาใช้
                if not chosen_snippet:
                    left_bound = max(0, indices[0] - 300)
                    right_bound = min(len(html_content), indices[0] + 300)
                    chosen_snippet = html_content[left_bound:right_bound]
                
                # 🎨 ตรวจจับคำสเตตัสและคลาสสีจากก้อนเนื้อหาที่คัดเลือกมา
                working_keys = ["working", "online", "updated", "safe", "active", "operational", "🟢", "green", "emerald", "lime", "success", "text-green", "bg-green"]
                patched_keys = ["patched", "updating", "maintenance", "🟠", "orange", "amber", "yellow", "warning", "text-orange", "text-amber"]
                
                if any(wk in chosen_snippet for wk in working_keys):
                    status_str = "🟢 Working"
                elif any(pk in chosen_snippet for pk in patched_keys):
                    status_str = "🟠 Patched"
                else:
                    status_str = "🔴 Down"
                    
                categorized_executors[platform].append(f"**{name}** : {status_str}")
                
        return "ONLINE", categorized_executors

    except Exception as e:
        print(f"[{time.strftime('%X')}] บอทเกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
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
                "description": f"**🌐 สถานะเว็บไซต์ (weao.xyz):** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE'}\n\n"
                               f"ระบบสแกนวิเคราะห์โค้ดและดักจับคลาสสีหน้าเว็บโดยตรงแบบ Real-time",
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
    print("=== ระบบสแกนพิกัดรอบทิศทาง (Smart-Window Scraping v4) เริ่มทำงาน ===")

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
                    print(f"[{time.strftime('%X')}] อัปเดตสถานะตรงตามพิกัดหน้าเว็บเรียบร้อย")
                elif response.status_code == 404:
                    message_id = None
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()

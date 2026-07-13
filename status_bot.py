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
API_URL = "https://weao.xyz/api/status" # (ใส่ URL API ของเว็บ weao.xyz ที่ใช้ดึงข้อมูล JSON)
CHECK_INTERVAL = 30  
FOOTER_TEXT = "Vereus X Status System"
# =======================================================

app = Flask('')

@app.route('/')
def home():
    return "<h1>Vereus X Status System v5 (Webhook Only) is Active!</h1>", 200

def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def fetch_weao_api():
    """ดึงข้อมูล JSON จาก API ของ weao.xyz โดยตรง (ดักจับตัวใหม่ได้อัตโนมัติ)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # ดึงข้อมูลจาก API
        response = requests.get(API_URL, timeout=15, headers=headers)
        
        if response.status_code == 200:
            return "ONLINE", response.json()
        else:
            return "OFFLINE", None
            
    except Exception as e:
        print(f"[{time.strftime('%X')}] บอทเกิดข้อผิดพลาดในการเชื่อมต่อ API: {e}")
        return "OFFLINE", None

def build_embed(web_status, api_data):
    # ตั้งค่าสี Embed ตามสถานะเว็บ
    embed_color = 65280 if web_status == "ONLINE" else 16711680
    current_time_str = time.strftime('%X')
    
    embed = {
        "title": "🛡️ Executor Status by siw",
        "description": f"🌐 **WEBSITE WEAO STATUS:** {'🟢 ONLINE' if web_status == 'ONLINE' else '🔴 OFFLINE'}\n\n"
                       f"🟢 Working = UPDATE | 🟠 Issues = WAITING FIX | 🔴 Patched = DOWN",
        "color": embed_color,
        "fields": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": f"{FOOTER_TEXT} | อัปเดตล่าสุด: {current_time_str}"}
    }

    if not api_data:
        embed["fields"].append({"name": "⚠️ System Warning", "value": "ไม่สามารถดึงข้อมูลจาก API ได้ในขณะนี้", "inline": False})
        return {"embeds": [embed]}

    # สมมติโครงสร้าง JSON ว่ามีคีย์ 'exploits' ที่เก็บรายชื่อตัวรันทั้งหมด
    # โค้ดส่วนนี้จะวนลูปตัวรันทั้งหมด (มีตัวใหม่ก็จะถูกเพิ่มอัตโนมัติ)
    categories = {}
    
    exploits_list = api_data.get("exploits", [])
    
    for item in exploits_list:
        name = item.get("name", "Unknown")
        version = item.get("version", "N/A")
        price = item.get("price", "Free")
        status_raw = item.get("status", "").lower()
        os_type = item.get("os", "Windows") # จัดหมวดหมู่ตาม OS
        
        # จัดการข้อมูลสเตตัส
        if status_raw in ["updated", "working", "active", "online"]:
            status_icon = "🟢"
            status_text = "Working"
        elif status_raw in ["issues", "waiting fix", "maintenance"]:
            status_icon = "🟠"
            status_text = "Issues"
        else:
            status_icon = "🔴"
            status_text = "Patched"

        # ดึงข้อมูลเชิงลึก
        sunc = item.get("sunc", "N/A")
        unc = item.get("unc", "N/A")
        decomp = "✅" if item.get("decompiler") else "❌"
        multi = "✅" if item.get("multi_instance") else "❌"
        raknet = "✅" if item.get("raknet") else "❌"
        
        web_link = item.get("website", "")
        discord_link = item.get("discord", "")
        purchase_link = item.get("purchase", "")

        # สร้างข้อความสำหรับตัวรัน 1 ตัว
        # ใช้รูปแบบ Markdown Links [ชื่อ](ลิ้งก์) เพื่อให้คลิกได้และไม่รก
        links_str = []
        if web_link: links_str.append(f"[Website]({web_link})")
        if discord_link: links_str.append(f"[Discord]({discord_link})")
        if purchase_link: links_str.append(f"[Purchase]({purchase_link})")
        links_formatted = " | ".join(links_str) if links_str else "No Links"

        # จัดฟอร์แมตข้อความให้โชว์ทุกอย่าง
        entry = f"{status_icon} **{name}** `[{version}]` - {price}\n"
        entry += f"┣ 📊 sUNC: `{sunc}%` | UNC: `{unc}%`\n"
        entry += f"┣ 🛠️ Decomp: {decomp} | Multi: {multi} | Raknet: {raknet}\n"
        entry += f"┗ 🔗 {links_formatted}\n"

        if os_type not in categories:
            categories[os_type] = []
        categories[os_type].append(entry)

    # เพิ่ม Field ลงใน Embed ตามหมวดหมู่ (Windows, Mac, Android, ฯลฯ)
    # หมายเหตุ: Discord จำกัดข้อความใน 1 Field ที่ 1024 ตัวอักษร หากตัวรันในหมวดนั้นยาวเกินไป อาจจะต้องเขียนแยก (ในโค้ดนี้รวบยอดให้ก่อน)
    for os_name, items in categories.items():
        # ถ้าข้อความยาวเกิน 1000 ตัวอักษร ให้แยก Field (ป้องกัน Webhook Error)
        chunk_text = ""
        part = 1
        for i, text in enumerate(items):
            if len(chunk_text) + len(text) > 950:
                embed["fields"].append({
                    "name": f"💻 {os_name} Script Executor Exploits (Part {part})",
                    "value": chunk_text,
                    "inline": False
                })
                chunk_text = text + "\n"
                part += 1
            else:
                chunk_text += text + "\n"
        
        if chunk_text:
            title = f"💻 {os_name} Script Executor Exploits" if part == 1 else f"💻 {os_name} Script Executor Exploits (Part {part})"
            embed["fields"].append({"name": title, "value": chunk_text, "inline": False})

    return {"embeds": [embed]}

def monitor_loop():
    message_id = None
    webhook_url_with_wait = WEBHOOK_URL + ("" if "?wait=true" in WEBHOOK_URL else "?wait=true")
    time.sleep(3)
    print("=== ระบบดึงข้อมูล API และโชว์รายละเอียดครบจบใน Webhook เริ่มทำงาน ===")

    while True:
        web_status, api_data = fetch_weao_api()
        payload = build_embed(web_status, api_data)
        
        try:
            if message_id is None:
                # ส่งข้อความใหม่
                response = requests.post(webhook_url_with_wait, json=payload)
                if response.status_code in [200, 201]:
                    message_id = response.json().get("id")
                    print(f"[{time.strftime('%X')}] สร้างข้อความหลักสำเร็จ (ID: {message_id})")
            else:
                # อัปเดตข้อความเดิม
                clean_url = WEBHOOK_URL.split('?')[0]
                edit_url = f"{clean_url}/messages/{message_id}"
                response = requests.patch(edit_url, json=payload)
                
                if response.status_code == 200:
                    print(f"[{time.strftime('%X')}] อัปเดตสถานะและข้อมูลเชิงลึกเรียบร้อย")
                elif response.status_code == 404:
                    # ถ้าข้อความโดนลบไปแล้ว ให้ส่งใหม่ในรอบหน้า
                    message_id = None
        except Exception as e:
            print(f"Discord Webhook Error: {e}")
            
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    server_thread = Thread(target=keep_alive)
    server_thread.start()
    monitor_loop()
